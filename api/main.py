"""
API RAG - Recherche et génération de réponses
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import httpx
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Config
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost')
COLLECTION_NAME = 'documents'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
OLLAMA_MODEL = 'mistral'

# Clients
qdrant = QdrantClient(host=QDRANT_HOST, port=6333)
embedder = SentenceTransformer(EMBEDDING_MODEL)

class QueryRequest(BaseModel):
    question: str
    top_k: int = 3

class Source(BaseModel):
    text: str
    source: str
    page: int

class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    confidence: float

@app.get("/")
def root():
    return {"message": "📚 RAG API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy", "qdrant": qdrant.get_collections() is not None}

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Pose une question et retourne une réponse avec sources"""
    logger.info(f"❓ Question: {request.question}")
    
    try:
        # 1. Embedding de la question
        query_vector = embedder.encode(request.question).tolist()
        
        # 2. Recherche dans Qdrant
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=request.top_k
        )
        
        if not results:
            return QueryResponse(
                answer="Je n'ai pas trouvé d'information pertinente dans les documents.",
                sources=[],
                confidence=0.0
            )
        
        # 3. Préparer le contexte
        context = "\n\n---\n\n".join([
            f"[Document {i+1}] (source: {r.payload['source']}, page {r.payload.get('page', '?')}):\n{r.payload['text']}"
            for i, r in enumerate(results)
        ])
        
        # 4. Prompt pour le LLM
        prompt = f"""Tu es un assistant qui répond aux questions en te basant UNIQUEMENT sur le contexte fourni.

CONTEXTE:
{context}

QUESTION: {request.question}

INSTRUCTIONS:
- Réponds en français de manière claire et concise
- Base-toi UNIQUEMENT sur le contexte ci-dessus
- Si l'information n'est pas dans le contexte, dis "Je ne trouve pas cette information dans les documents"
- Cite les sources quand c'est pertinent
- Ne pas inventer d'informations

RÉPONSE:"""
        
        # 5. Appel à Ollama
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"http://{OLLAMA_HOST}:11434/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            llm_response = response.json()
            answer = llm_response.get("response", "Erreur de génération")
        
        # 6. Sources
        sources = [
            Source(
                text=r.payload['text'][:200] + "...",
                source=r.payload['source'],
                page=r.payload.get('page', 0)
            )
            for r in results
        ]
        
        # 7. Score de confiance (basé sur les scores de similarité)
        avg_score = sum(r.score for r in results) / len(results)
        
        logger.info(f"✅ Réponse générée (confiance: {avg_score:.2f})")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=round(avg_score, 2)
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))