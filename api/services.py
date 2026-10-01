"""
Services externes : Qdrant, Embeddings et Ollama , connexions à Qdrant, Ollama, Sentence Transformers
"""

import logging
import httpx
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    """Service pour interagir avec Qdrant"""

    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.COLLECTION_NAME
        logger.info(f"Qdrant connecté sur {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")

    def health_check(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status.value if hasattr(info.status, 'value') else str(info.status)
            }
        except Exception as e:
            logger.error(f"Erreur get_collection_info: {e}")
            return {"name": self.collection_name, "points_count": 0, "error": str(e)}

    def search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                with_payload=True
            )
            return [
                {
                    "text": r.payload.get("text", ""),
                    "source": r.payload.get("source", "unknown"),
                    "page": r.payload.get("page", 1),
                    "chunk_id": r.payload.get("chunk_id"),
                    "score": r.score
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Erreur search: {e}")
            return []


class EmbeddingService:
    """Service pour générer les embeddings"""

    def __init__(self):
        logger.info(f"Chargement du modèle {settings.EMBEDDING_MODEL}...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info(f"Modèle chargé (dim: {self.model.get_sentence_embedding_dimension()})")

    def encode(self, text: str) -> List[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()


class OllamaService:
    """Service pour interagir avec Ollama"""

    def __init__(self):
        self.base_url = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
        self.model = settings.OLLAMA_MODEL
        logger.info(f"Ollama configuré sur {self.base_url} avec {self.model}")

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Erreur list_models: {e}")
            return []

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )
                if response.status_code != 200:
                    logger.error(f"Ollama erreur {response.status_code}: {response.text}")
                    return "Erreur de génération"
                data = response.json()
                return data.get("response", "").strip()
        except httpx.TimeoutException:
            logger.error("Timeout Ollama")
            return "Timeout : le modèle a mis trop de temps à répondre"
        except Exception as e:
            logger.error(f"Erreur generate: {e}")
            return f"Erreur: {str(e)}"


# Instances globales (singletons)
qdrant_service = QdrantService()
embedding_service = EmbeddingService()
ollama_service = OllamaService()
