"""Fonctions utilitaires pour l'interface Streamlit."""

import math
import os
from typing import Any, Dict, Optional

import requests


API_URL = os.getenv("API_URL", "http://localhost:8000").strip().rstrip("/")
if not API_URL:
    API_URL = "http://localhost:8000"


def _request_json(method: str, path: str, timeout: Any, **kwargs: Any) -> Dict[str, Any]:
    """Envoie une requête et valide la forme JSON de la réponse."""
    response = requests.request(method, f"{API_URL}{path}", timeout=timeout, **kwargs)
    try:
        payload = response.json()
    except ValueError as exc:
        if not response.ok:
            raise requests.HTTPError(f"HTTP {response.status_code}", response=response) from exc
        raise ValueError("La réponse de l'API n'est pas un JSON valide.") from exc

    if not response.ok:
        raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
    if not isinstance(payload, dict):
        raise ValueError("La réponse de l'API a un format inattendu.")
    return payload


def api_query(question: str, top_k: int = 3, temperature: float = 0.1) -> Dict[str, Any]:
    """Appelle l'endpoint /query de l'API."""
    try:
        payload = _request_json(
            "POST",
            "/query",
            timeout=(5, 600),
            json={
                "question": question,
                "top_k": top_k,
                "temperature": temperature,
                "include_sources": True,
            },
        )
        if not isinstance(payload.get("answer"), str):
            return {"error": "La réponse de l'API ne contient pas de réponse valide."}
        return payload
    except requests.exceptions.Timeout:
        return {"error": "Délai dépassé : le modèle a mis trop de temps à répondre."}
    except requests.exceptions.ConnectionError:
        return {"error": "Impossible de joindre l'API. Vérifiez son état et le réseau Docker."}
    except requests.exceptions.HTTPError as exc:
        return {"error": f"L'API a renvoyé une erreur ({exc})."}
    except (requests.exceptions.RequestException, ValueError) as exc:
        return {"error": f"Réponse invalide de l'API : {exc}"}


def api_health() -> Optional[Dict[str, Any]]:
    """Vérifie l'état de l'API."""
    try:
        return _request_json("GET", "/health", timeout=(3, 10))
    except requests.exceptions.HTTPError as exc:
        return {"status": "error", "error": f"Erreur HTTP ({exc})."}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "Délai dépassé lors de la vérification."}
    except (requests.exceptions.ConnectionError, ValueError, requests.exceptions.RequestException):
        return None


def api_stats() -> Optional[Dict[str, Any]]:
    """Récupère les statistiques."""
    try:
        return _request_json("GET", "/stats", timeout=(3, 10))
    except (requests.exceptions.RequestException, ValueError):
        return None


def api_search(query: str, top_k: int = 5) -> Dict[str, Any]:
    """Recherche sans génération LLM."""
    try:
        payload = _request_json(
            "POST",
            "/search",
            timeout=(5, 30),
            json={"query": query, "top_k": top_k},
        )
        if not isinstance(payload.get("results"), list):
            return {"error": "La réponse de recherche a un format inattendu."}
        return payload
    except requests.exceptions.Timeout:
        return {"error": "Délai dépassé pendant la recherche."}
    except requests.exceptions.ConnectionError:
        return {"error": "Impossible de joindre l'API. Vérifiez son état et le réseau Docker."}
    except requests.exceptions.HTTPError as exc:
        return {"error": f"L'API a renvoyé une erreur ({exc})."}
    except (requests.exceptions.RequestException, ValueError) as exc:
        return {"error": f"Réponse invalide de l'API : {exc}"}


def get_confidence_class(confidence: float) -> str:
    """Retourne la classe CSS selon le score."""
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return "confidence-low"
    if not math.isfinite(value):
        return "confidence-low"
    if value >= 0.7:
        return "confidence-high"
    if value >= 0.4:
        return "confidence-medium"
    return "confidence-low"


def get_confidence_label(confidence: float) -> str:
    """Retourne le libellé selon le score."""
    try:
        value = float(confidence)
    except (TypeError, ValueError):
        return "Faible"
    if not math.isfinite(value):
        return "Faible"
    if value >= 0.7:
        return "Élevée"
    if value >= 0.4:
        return "Moyenne"
    return "Faible"


def format_time(seconds: float) -> str:
    """Formate une durée en millisecondes, secondes ou minutes."""
    value = float(seconds)
    if not math.isfinite(value):
        return "Durée inconnue"
    value = max(value, 0.0)
    if value < 1:
        return f"{value * 1000:.0f} ms"
    if value < 60:
        return f"{value:.1f} s"
    minutes = int(value // 60)
    remaining_seconds = value % 60
    return f"{minutes}m {remaining_seconds:.0f}s"


def export_conversation(messages: list) -> str:
    """Exporte la conversation en Markdown."""
    from datetime import datetime

    markdown = "# Conversation - Assistant Documentaire\n\n"
    markdown += f"*Exporté le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*\n\n---\n\n"

    for message in messages:
        if not isinstance(message, dict):
            continue
        content = str(message.get("content", ""))
        if message.get("role") == "user":
            markdown += f"## Utilisateur\n\n{content}\n\n"
            continue

        markdown += f"## Assistant\n\n{content}\n\n"
        try:
            confidence = float(message.get("confidence"))
        except (TypeError, ValueError):
            confidence = None
        if confidence is not None and math.isfinite(confidence):
            markdown += f"*Confiance : {min(max(confidence, 0.0), 1.0) * 100:.0f}%*\n\n"

        sources = message.get("sources", [])
        if isinstance(sources, list) and sources:
            markdown += "### Sources\n\n"
            for index, source in enumerate(sources, 1):
                if not isinstance(source, dict):
                    continue
                try:
                    score = float(source.get("score", 0))
                except (TypeError, ValueError):
                    score = 0.0
                if not math.isfinite(score):
                    score = 0.0
                markdown += (
                    f"**{index}. {source.get('source', 'inconnue')}** "
                    f"(page {source.get('page', 1)}) - score : {score:.3f}\n\n"
                )
                markdown += f"> {str(source.get('text', ''))[:200]}...\n\n"
        markdown += "---\n\n"

    return markdown
