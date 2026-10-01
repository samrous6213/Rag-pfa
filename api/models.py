"""
Modèles Pydantic pour l'API RAG
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Requête de question à l'API"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="La question à poser",
        examples=["Quels sont les horaires de télétravail ?"]
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Nombre de documents à récupérer")
    include_sources: bool = Field(default=True, description="Inclure les sources dans la réponse")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Température du LLM")


class Source(BaseModel):
    """Source d'un document"""
    text: str = Field(..., description="Extrait du document")
    source: str = Field(..., description="Nom du fichier source")
    page: int = Field(default=1, description="Numéro de page")
    score: float = Field(..., description="Score de similarité")
    chunk_id: Optional[int] = Field(default=None, description="ID du chunk")


class QueryResponse(BaseModel):
    """Réponse de l'API"""
    answer: str = Field(..., description="Réponse générée par le LLM")
    sources: List[Source] = Field(default_factory=list, description="Sources utilisées")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Score de confiance")
    processing_time: float = Field(..., description="Temps de traitement en secondes")
    model: str = Field(..., description="Modèle utilisé")
    timestamp: datetime = Field(default_factory=datetime.now)


class SearchRequest(BaseModel):
    """Requête de recherche (sans génération)"""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    """Résultat de recherche"""
    text: str
    source: str
    page: int
    score: float


class SearchResponse(BaseModel):
    """Réponse de recherche"""
    results: List[SearchResult]
    total: int
    query: str


class HealthResponse(BaseModel):
    """Réponse du health check"""
    status: str
    services: dict
    timestamp: datetime = Field(default_factory=datetime.now)


class StatsResponse(BaseModel):
    """Statistiques de l'API"""
    total_documents: int
    total_queries: int
    avg_response_time: float
    collection_name: str
    embedding_model: str
    llm_model: str
