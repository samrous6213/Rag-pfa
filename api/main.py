"""
API RAG - Point d'entrée FastAPI
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from models import (
    QueryRequest, QueryResponse,
    SearchRequest, SearchResponse, SearchResult,
    HealthResponse, StatsResponse
)
from services import qdrant_service, ollama_service, embedding_service
from rag import answer_question, search_only


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Actions au démarrage et à l'arrêt"""
    logger.info("Démarrage de l'API RAG...")

    if qdrant_service.health_check():
        logger.info("Qdrant est accessible")
    else:
        logger.warning("Qdrant n'est pas accessible")

    if await ollama_service.health_check():
        models = await ollama_service.list_models()
        logger.info(f"Ollama est accessible (modèles: {models})")
    else:
        logger.warning("Ollama n'est pas accessible")

    info = qdrant_service.get_collection_info()
    logger.info(f"Collection : {info}")

    logger.info("API prête !")

    yield

    logger.info("Arrêt de l'API")


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Ajoute le temps de traitement dans les headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response


@app.get("/", tags=["Général"])
async def root():
    """Point d'entrée de l'API"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "stats": "/stats",
            "query": "/query (POST)",
            "search": "/search (POST)"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Général"])
async def health():
    """Vérifie l'état des services"""
    qdrant_ok = qdrant_service.health_check()
    ollama_ok = await ollama_service.health_check()

    status = "healthy" if (qdrant_ok and ollama_ok) else "degraded"

    return HealthResponse(
        status=status,
        services={
            "qdrant": "connected" if qdrant_ok else "disconnected",
            "ollama": "connected" if ollama_ok else "disconnected",
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.OLLAMA_MODEL
        }
    )


@app.get("/stats", response_model=StatsResponse, tags=["Général"])
async def stats():
    """Statistiques de l'API"""
    info = qdrant_service.get_collection_info()

    return StatsResponse(
        total_documents=info.get("points_count", 0),
        total_queries=0,
        avg_response_time=0.0,
        collection_name=settings.COLLECTION_NAME,
        embedding_model=settings.EMBEDDING_MODEL,
        llm_model=settings.OLLAMA_MODEL
    )


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query(request: QueryRequest):
    """
    Pose une question et obtient une réponse RAG avec sources.
    """
    logger.info(f"POST /query - Question: {request.question}")

    try:
        result = await answer_question(
            question=request.question,
            top_k=request.top_k,
            temperature=request.temperature,
            include_sources=request.include_sources
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Erreur /query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse, tags=["Recherche"])
async def search(request: SearchRequest):
    """
    Recherche des documents similaires SANS génération LLM.
    """
    logger.info(f"POST /search - Query: {request.query}")

    try:
        result = search_only(request.query, request.top_k)

        return SearchResponse(
            results=[SearchResult(**r) for r in result["results"]],
            total=result["total"],
            query=result["query"]
        )

    except Exception as e:
        logger.error(f"Erreur /search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestion globale des erreurs"""
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
