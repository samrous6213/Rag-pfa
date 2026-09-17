"""
Script d'ingestion des documents dans Qdrant
Utilise LangChain pour le chunking et Sentence Transformers pour les embeddings
"""

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
COLLECTION_NAME = 'documents'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def load_documents(directory: str):
    """Charge tous les documents d'un dossier"""
    documents = []
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if filename.endswith('.pdf'):
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            documents.extend(docs)
            logger.info(f"📄 PDF chargé : {filename} ({len(docs)} pages)")
            
        elif filename.endswith('.txt'):
            loader = TextLoader(filepath, encoding='utf-8')
            docs = loader.load()
            documents.extend(docs)
            logger.info(f"📝 TXT chargé : {filename}")
    
    return documents

def chunk_documents(documents):
    """Découpe les documents en chunks avec overlap"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = splitter.split_documents(documents)
    logger.info(f"✂️ {len(chunks)} chunks créés")
    return chunks

def create_embeddings(chunks):
    """Génère les embeddings pour chaque chunk"""
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    texts = [chunk.page_content for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    logger.info(f"🔢 {len(embeddings)} embeddings générés (dim: {embeddings.shape[1]})")
    return embeddings

def store_in_qdrant(chunks, embeddings):
    """Stocke les vecteurs et métadonnées dans Qdrant"""
    client = QdrantClient(host=QDRANT_HOST, port=6333)
    
    # Recréer la collection
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=embeddings.shape[1],
            distance=models.Distance.COSINE
        )
    )
    
    # Préparer les points
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            models.PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={
                    'text': chunk.page_content,
                    'source': chunk.metadata.get('source', 'unknown'),
                    'page': chunk.metadata.get('page', 0)
                }
            )
        )
    
    # Insérer par batch
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    
    logger.info(f"✅ {len(points)} vecteurs stockés dans Qdrant")

if __name__ == "__main__":
    # Chemins
    docs_dir = '/opt/airflow/data/documents'
    
    # Pipeline
    logger.info("🚀 Démarrage de l'ingestion...")
    documents = load_documents(docs_dir)
    chunks = chunk_documents(documents)
    embeddings = create_embeddings(chunks)
    store_in_qdrant(chunks, embeddings)
    logger.info("✅ Ingestion terminée !")