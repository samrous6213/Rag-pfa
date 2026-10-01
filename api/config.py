"""
Configuration centralisée de l'API RAG , variables de configuration (hosts, ports, seuils)
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuration de l'application"""

    # API
    API_TITLE = "RAG API - Assistant Documentaire"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = """
    API RAG (Retrieval Augmented Generation) pour interroger des documents.

    ## Fonctionnalités
    - Recherche sémantique dans les documents
    - Génération de réponses avec Mistral 7B
    - Citation des sources
    - Score de confiance
    """

    # Qdrant
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "documents")

    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "localhost")
    OLLAMA_PORT: int = int(os.getenv("OLLAMA_PORT", 11434))
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")

    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # RAG
    DEFAULT_TOP_K: int = 3
    MAX_TOP_K: int = 10
    MIN_SCORE_THRESHOLD: float = 0.3
    MAX_CONTEXT_LENGTH: int = 4000

    # Timeouts
    OLLAMA_TIMEOUT: int = 120


settings = Settings()
