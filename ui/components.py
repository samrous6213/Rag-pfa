"""Composants réutilisables pour l'interface Streamlit."""

import html
import math
from typing import Any, Dict, List, Optional

import streamlit as st

from utils import format_time, get_confidence_class, get_confidence_label


def render_header() -> None:
    """Affiche le header principal."""
    st.markdown(
        """
        <div class="main-header">
            <h1>Assistant Documentaire Intelligent</h1>
            <p>Posez vos questions en langage naturel et obtenez des réponses basées sur vos documents</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_user_message(message: str) -> None:
    """Affiche un message utilisateur en échappant son contenu."""
    safe_message = html.escape(str(message)).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="chat-message user-message">
            <span class="message-author">Vous</span>
            <div class="message-body">{safe_message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_assistant_message(
    answer: str,
    confidence: Optional[float] = None,
    processing_time: Optional[float] = None,
    model: Optional[str] = None,
) -> None:
    """Affiche une réponse assistant sans interpréter son HTML."""
    safe_answer = html.escape(str(answer)).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="chat-message assistant-message">
            <span class="message-author">Assistant</span>
            <div class="message-body">{safe_answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        confidence_value = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence_value = None

    if confidence_value is not None and math.isfinite(confidence_value):
        confidence_value = min(max(confidence_value, 0.0), 1.0)
        confidence_class = get_confidence_class(confidence_value)
        confidence_label = get_confidence_label(confidence_value)
        confidence_percent = int(confidence_value * 100)
        st.markdown(
            f"""
            <div class="confidence-bar" style="margin-top: -8px; margin-bottom: 12px; padding: 0 4px;">
                <div style="font-size: 0.8rem; color: #71717a; margin-bottom: 4px;">Confiance : {confidence_label} ({confidence_percent}%)</div>
                <div class="confidence-fill {confidence_class}">
                    <div style="width: {confidence_percent}%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    metadata = []
    try:
        if processing_time is not None:
            metadata.append(f"Traitement : {format_time(float(processing_time))}")
    except (TypeError, ValueError, OverflowError):
        pass
    if model is not None:
        metadata.append(f"Modèle : {html.escape(str(model))}")

    if metadata:
        st.markdown(
            f"""
            <div class="message-meta" style="margin-bottom: 16px;">
                {' • '.join(metadata)}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sources(sources: List[Dict[str, Any]]) -> None:
    """Affiche les sources en échappant les données provenant de l'API."""
    if not sources:
        return

    with st.expander(f"Sources utilisées ({len(sources)})", expanded=False):
        for source in sources:
            if not isinstance(source, dict):
                continue
            try:
                score = float(source.get("score", 0))
            except (TypeError, ValueError):
                score = 0.0
            if not math.isfinite(score):
                score = 0.0

            score_class = "" if score >= 0.7 else "low"
            source_name = html.escape(str(source.get("source", "inconnue")))
            source_page = html.escape(str(source.get("page", 1)))
            source_chunk = html.escape(str(source.get("chunk_id", "?")))
            source_text = html.escape(str(source.get("text", "")))
            st.markdown(
                f"""
                <div class="source-card">
                    <div class="source-header">
                        <span class="source-name">{source_name}</span>
                        <span class="source-score {score_class}">Score : {score:.2f}</span>
                    </div>
                    <div class="source-details">Page {source_page} • Chunk {source_chunk}</div>
                    <div class="source-text">"{source_text}"</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_sidebar_stats(stats: Dict[str, Any]) -> None:
    """Affiche les statistiques dans la sidebar."""
    if not stats:
        st.sidebar.warning("Statistiques indisponibles")
        return

    st.sidebar.markdown("### Statistiques")
    first_column, second_column = st.sidebar.columns(2)
    with first_column:
        st.metric("Documents", stats.get("total_documents", 0))
    with second_column:
        st.metric("Requêtes", stats.get("total_queries", 0))


def render_health_status(health: Optional[Dict[str, Any]]) -> None:
    """Affiche l'état des services."""
    if not health:
        st.sidebar.error("API inaccessible")
        return

    status = health.get("status")
    if status == "healthy":
        st.sidebar.success("Tous les services opérationnels")
    elif status == "degraded":
        st.sidebar.warning("Services en mode dégradé")
    elif status in ("error", "timeout"):
        st.sidebar.warning("API joignable, état indisponible")
    else:
        st.sidebar.error("État de l'API inconnu")

    services = health.get("services", {})
    if not isinstance(services, dict):
        services = {}
    with st.sidebar.expander("Détails techniques"):
        for name, state in services.items():
            state_label = "Connecté" if state in ("connected", "healthy") else "Déconnecté"
            st.text(f"{name} : {state_label}")


def render_suggestions() -> Optional[str]:
    """Affiche les boutons de suggestions rapides."""
    st.markdown("**Suggestions :**")
    suggestions = (
        ("Quels sont les horaires de télétravail ?", "Quels sont les horaires de télétravail ?"),
        ("Combien de jours de congés ?", "Combien de jours de congés annuels ?"),
        ("Comment fonctionne la mutuelle ?", "Comment fonctionne la mutuelle ?"),
        ("Quelle est l'architecture technique ?", "Quelle est l'architecture technique du système ?"),
    )
    for label, question in suggestions:
        if st.button(label, use_container_width=True):
            return question
    return None
