"""
Fonctions utilitaires pour l'UI
"""

import os
import requests
from typing import Optional, Dict, Any

API_URL = os.getenv("API_URL", "http://localhost:8000")


def api_query(question: str, top_k: int = 3, temperature: float = 0.1) -> Optional[Dict[str, Any]]:
    """Appelle l'endpoint /query de l'API"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={
                "question": question,
                "top_k": top_k,
                "temperature": temperature,
                "include_sources": True
            },
            timeout=180
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Timeout : le modèle a mis trop de temps à répondre"}
    except requests.exceptions.ConnectionError:
        return {"error": "Impossible de se connecter à l'API. Vérifiez qu'elle est lancée."}
    except Exception as e:
        return {"error": f"Erreur : {str(e)}"}


def api_health() -> Optional[Dict[str, Any]]:
    """Vérifie l'état de l'API"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def api_stats() -> Optional[Dict[str, Any]]:
    """Récupère les statistiques"""
    try:
        response = requests.get(f"{API_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def api_search(query: str, top_k: int = 5) -> Optional[Dict[str, Any]]:
    """Recherche sans génération LLM"""
    try:
        response = requests.post(
            f"{API_URL}/search",
            json={"query": query, "top_k": top_k},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def get_confidence_class(confidence: float) -> str:
    """Retourne la classe CSS selon le score"""
    if confidence >= 0.7:
        return "confidence-high"
    elif confidence >= 0.4:
        return "confidence-medium"
    else:
        return "confidence-low"


def get_confidence_label(confidence: float) -> str:
    """Retourne le label selon le score"""
    if confidence >= 0.7:
        return "Élevée"
    elif confidence >= 0.4:
        return "Moyenne"
    else:
        return "Faible"


def format_time(seconds: float) -> str:
    """Formate le temps"""
    if seconds < 1:
        return f"{seconds*1000:.0f} ms"
    elif seconds < 60:
        return f"{seconds:.1f} s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"