"""
Script d'ingestion des documents dans Qdrant
Supporte : PDF, TXT
Utilise LangChain pour le chunking et Sentence Transformers pour les embeddings
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from minio import Minio

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
MINIO_HOST = os.getenv('MINIO_HOST', 'minio:9000')
MINIO_USER = os.getenv('MINIO_ROOT_USER', 'minioadmin')
MINIO_PASSWORD = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'documents')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
DOCS_DIR = os.getenv('DOCS_DIR', '/opt/airflow/data/documents')
BUCKET_NAME = 'documents-raw'


def get_minio_client():
    """Crée un client MinIO"""
    return Minio(
        MINIO_HOST,
        access_key=MINIO_USER,
        secret_key=MINIO_PASSWORD,
        secure=False
    )


def upload_to_minio(filepath: str):
    """Upload un fichier dans MinIO"""
    try:
        client = get_minio_client()

        if not client.bucket_exists(BUCKET_NAME):
            client.make_bucket(BUCKET_NAME)
            logger.info(f"📦 Bucket '{BUCKET_NAME}' créé")

        filename = os.path.basename(filepath)
        client.fput_object(BUCKET_NAME, filename, filepath)
        logger.info(f"☁️ {filename} uploadé dans MinIO")
        return True

    except Exception as e:
        logger.error(f"❌ Erreur MinIO: {e}")
        return False


def load_documents(directory: str):
    """Charge tous les documents d'un dossier"""
    documents = []
    directory = Path(directory)

    if not directory.exists():
        logger.error(f"❌ Dossier introuvable: {directory}")
        return []

    for filepath in directory.iterdir():
        if filepath.is_dir():
            continue

        try:
            if filepath.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(filepath))
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"📄 PDF chargé : {filepath.name} ({len(docs)} pages)")

            elif filepath.suffix.lower() == '.txt':
                loader = TextLoader(str(filepath), encoding='utf-8')
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"📝 TXT chargé : {filepath.name}")

            else:
                logger.warning(f"⚠️ Format non supporté : {filepath.name}")

        except Exception as e:
            logger.error(f"❌ Erreur avec {filepath.name}: {e}")

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
    logger.info(f"🔢 Chargement du modèle {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [chunk.page_content for chunk in chunks]
    logger.info(f"🔢 Génération des embeddings pour {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    logger.info(f"✅ {len(embeddings)} embeddings générés (dim: {embeddings.shape[1]})")
    return embeddings, model


def store_in_qdrant(chunks, embeddings):
    """Stocke les vecteurs et métadonnées dans Qdrant"""
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    logger.info(f"💾 Création de la collection '{COLLECTION_NAME}'...")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=embeddings.shape[1],
            distance=models.Distance.COSINE
        )
    )

    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        source = chunk.metadata.get('source', 'unknown')
        source_name = os.path.basename(source)
        page = chunk.metadata.get('page', 0)

        points.append(
            models.PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={
                    'text': chunk.page_content,
                    'source': source_name,
                    'page': page + 1 if page else 1,
                    'chunk_id': i,
                    'ingested_at': datetime.now().isoformat()
                }
            )
        )

    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        logger.info(f"   → Batch {i//batch_size + 1}: {len(batch)} points insérés")

    logger.info(f"✅ {len(points)} vecteurs stockés dans Qdrant")

    count = client.count(collection_name=COLLECTION_NAME).count
    logger.info(f"📊 Total dans Qdrant : {count} points")


def main():
    """Pipeline complet d'ingestion"""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("🚀 DÉMARRAGE DE L'INGESTION")
    logger.info("=" * 60)

    logger.info("\n📦 Étape 1: Upload dans MinIO")
    docs_path = Path(DOCS_DIR)
    if docs_path.exists():
        for filepath in docs_path.iterdir():
            if filepath.is_file() and filepath.suffix.lower() in ['.pdf', '.txt']:
                upload_to_minio(str(filepath))

    logger.info("\n📄 Étape 2: Chargement des documents")
    documents = load_documents(DOCS_DIR)

    if not documents:
        logger.error("❌ Aucun document à ingérer !")
        sys.exit(1)

    logger.info("\n✂️ Étape 3: Découpage en chunks")
    chunks = chunk_documents(documents)

    logger.info("\n🔢 Étape 4: Génération des embeddings")
    embeddings, _ = create_embeddings(chunks)

    logger.info("\n💾 Étape 5: Stockage dans Qdrant")
    store_in_qdrant(chunks, embeddings)

    duration = (datetime.now() - start_time).total_seconds()
    logger.info("\n" + "=" * 60)
    logger.info(f"✅ INGESTION TERMINÉE EN {duration:.1f} SECONDES")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
