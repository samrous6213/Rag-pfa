"""
Logique RAG : Retrieval + Augmentation + Generation
"""

import logging
import time
from typing import List, Dict, Any

from services import qdrant_service, embedding_service, ollama_service
from config import settings
from models import Source

logger = logging.getLogger(__name__)


# ===== PROMPTS =====

SYSTEM_PROMPT = """Tu es un assistant documentaire intelligent qui répond aux questions en français.

RÈGLES IMPORTANTES :
1. Réponds UNIQUEMENT en te basant sur le CONTEXTE fourni ci-dessous
2. Si l'information n'est pas dans le contexte, dis clairement : "Je ne trouve pas cette information dans les documents fournis."
3. Ne JAMAIS inventer d'informations
4. Sois précis et concis dans tes réponses
5. Cite les sources quand c'est pertinent (ex: "selon le document X")
6. Si le contexte contient des informations contradictoires, signale-le
7. Utilise un ton professionnel et neutre"""


def build_rag_prompt(question: str, context: str) -> str:
    """Construit le prompt RAG complet"""
    return f"""{SYSTEM_PROMPT}

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE :"""


def build_context(sources: List[Dict[str, Any]], max_length: int = None) -> str:
    """Construit le contexte à partir des sources"""
    max_length = max_length or settings.MAX_CONTEXT_LENGTH

    context_parts = []
    current_length = 0

    for i, source in enumerate(sources, 1):
        text = source["text"]
        source_name = source["source"]
        page = source.get("page", 1)
        score = source.get("score", 0)

        header = f"[Document {i}] (source: {source_name}, page {page}, pertinence: {score:.2f})"
        part = f"{header}\n{text}\n"

        if current_length + len(part) > max_length:
            break

        context_parts.append(part)
        current_length += len(part)

    return "\n---\n".join(context_parts)


def calculate_confidence(sources: List[Dict[str, Any]]) -> float:
    """Calcule le score de confiance basé sur les scores de similarité."""
    if not sources:
        return 0.0

    scores = [s.get("score", 0) for s in sources]

    weights = [1.0 / (i + 1) for i in range(len(scores))]
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)

    confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

    return min(max(confidence, 0.0), 1.0)


def format_sources(sources: List[Dict[str, Any]], max_text_length: int = 300) -> List[Source]:
    """Formate les sources pour la réponse"""
    formatted = []
    for s in sources:
        text = s["text"]
        if len(text) > max_text_length:
            text = text[:max_text_length] + "..."

        formatted.append(Source(
            text=text,
            source=s["source"],
            page=s.get("page", 1),
            score=round(s["score"], 4),
            chunk_id=s.get("chunk_id")
        ))
    return formatted


async def answer_question(
    question: str,
    top_k: int = 3,
    temperature: float = 0.1,
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Pipeline RAG complet :
    1. Embedding de la question
    2. Recherche dans Qdrant
    3. Construction du contexte
    4. Génération avec Ollama
    5. Formatage de la réponse
    """
    start_time = time.time()

    logger.info(f"Question : {question}")

    logger.info("Etape 1/4 : Embedding de la question...")
    query_vector = embedding_service.encode(question)

    logger.info(f"Etape 2/4 : Recherche des {top_k} documents les plus pertinents...")
    sources = qdrant_service.search(
        query_vector=query_vector,
        top_k=top_k,
        score_threshold=settings.MIN_SCORE_THRESHOLD
    )

    if not sources:
        logger.warning("Aucun document pertinent trouve")
        processing_time = time.time() - start_time
        return {
            "answer": "Je ne trouve pas cette information dans les documents fournis. Essayez de reformuler votre question ou de vérifier que les documents pertinents ont bien été ingérés.",
            "sources": [],
            "confidence": 0.0,
            "processing_time": round(processing_time, 2),
            "model": settings.OLLAMA_MODEL
        }

    logger.info(f"   -> {len(sources)} documents trouves (scores: {[round(s['score'], 3) for s in sources]})")

    logger.info("Etape 3/4 : Construction du prompt...")
    context = build_context(sources)
    prompt = build_rag_prompt(question, context)

    logger.info(f"Etape 4/4 : Generation avec {settings.OLLAMA_MODEL}...")
    answer = await ollama_service.generate(
        prompt=prompt,
        temperature=temperature
    )

    confidence = calculate_confidence(sources)

    processing_time = time.time() - start_time
    formatted_sources = format_sources(sources) if include_sources else []

    logger.info(f"Reponse generee en {processing_time:.2f}s (confiance: {confidence:.2f})")

    return {
        "answer": answer,
        "sources": formatted_sources,
        "confidence": round(confidence, 4),
        "processing_time": round(processing_time, 2),
        "model": settings.OLLAMA_MODEL
    }


def search_only(query: str, top_k: int = 5) -> Dict[str, Any]:
    """Recherche uniquement (sans génération LLM)"""
    logger.info(f"Recherche : {query}")

    query_vector = embedding_service.encode(query)
    results = qdrant_service.search(
        query_vector=query_vector,
        top_k=top_k
    )

    return {
        "results": results,
        "total": len(results),
        "query": query
    }
