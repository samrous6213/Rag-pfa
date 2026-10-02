"""
components.py - Composants réutilisables pour l'UI (Style minimaliste, chic et sans emojis)
"""

import streamlit as st
from typing import List, Dict, Any
from utils import get_confidence_class, get_confidence_label, format_time


def render_header():
    """Affiche le header principal"""
    st.markdown("""
    <div class="main-header">
        <h1>Assistant Documentaire Intelligent</h1>
        <p>Posez vos questions en langage naturel et obtenez des réponses basées sur vos documents</p>
    </div>
    """, unsafe_allow_html=True)


def render_user_message(message: str):
    """Affiche un message utilisateur"""
    st.markdown(f"""
    <div class="chat-message user-message">
        <span class="message-author">Vous</span>
        <div class="message-body">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_assistant_message(
    answer: str,
    confidence: float = None,
    processing_time: float = None,
    model: str = None
):
    """Affiche un message assistant sans fuite de balises HTML"""
    formatted_answer = answer.replace('\n', '<br>')
    
    st.markdown(f"""
    <div class="chat-message assistant-message">
        <span class="message-author">Assistant</span>
        <div class="message-body">{formatted_answer}</div>
    </div>
    """, unsafe_allow_html=True)

    if confidence is not None:
        conf_class = get_confidence_class(confidence)
        conf_label = get_confidence_label(confidence)
        conf_pct = int(confidence * 100)

        st.markdown(f"""
        <div class="confidence-bar" style="margin-top: -8px; margin-bottom: 12px; padding: 0 4px;">
            <div style="font-size: 0.8rem; color: #71717a; margin-bottom: 4px;">Confiance : {conf_label} ({conf_pct}%)</div>
            <div class="confidence-fill {conf_class}">
                <div style="width: {conf_pct}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    meta_parts = []
    if processing_time is not None:
        meta_parts.append(f"Traitement : {format_time(processing_time)}")
    if model is not None:
        meta_parts.append(f"Modèle : {model}")

    if meta_parts:
        meta_joined = " • ".join(meta_parts)
        st.markdown(f"""
        <div class="message-meta" style="margin-bottom: 16px;">
            {meta_joined}
        </div>
        """, unsafe_allow_html=True)


def render_sources(sources: List[Dict[str, Any]]):
    """Affiche les sources dans un expander"""
    if not sources:
        return

    with st.expander(f"Sources utilisées ({len(sources)})", expanded=False):
        for i, source in enumerate(sources, 1):
            score = source.get("score", 0)
            score_class = "" if score >= 0.7 else "low"
            src_name = source.get('source', 'unknown')
            src_page = source.get('page', 1)
            src_chunk = source.get('chunk_id', '?')
            src_text = source.get('text', '')

            st.markdown(f"""
            <div class="source-card">
                <div class="source-header">
                    <span class="source-name">{src_name}</span>
                    <span class="source-score {score_class}">Score : {score:.2f}</span>
                </div>
                <div class="source-details">
                    Page {src_page} • Chunk {src_chunk}
                </div>
                <div class="source-text">"{src_text}"</div>
            </div>
            """, unsafe_allow_html=True)


def render_sidebar_stats(stats: Dict[str, Any]):
    """Affiche les statistiques dans la sidebar"""
    if not stats:
        st.sidebar.warning("Statistiques indisponibles")
        return

    st.sidebar.markdown("### Statistiques")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Documents", stats.get("total_documents", 0))
    with col2:
        st.metric("Requêtes", stats.get("total_queries", 0))


def render_health_status(health: Dict[str, Any]):
    """Affiche l'état des services"""
    if not health:
        st.sidebar.error("API inaccessible")
        return

    status = health.get("status", "unknown")
    services = health.get("services", {})

    if status == "healthy":
        st.sidebar.success("Tous les services opérationnels")
    else:
        st.sidebar.warning("Services en mode dégradé")

    with st.sidebar.expander("Détails techniques"):
        for name, state in services.items():
            state_label = "Connecté" if state in ["connected", "healthy"] else "Déconnecté"
            st.markdown(f"**{name}** : {state_label}")


def render_suggestions():
    """Affiche uniquement les boutons de suggestions rapides"""
    col1, col2 = st.columns(2)
    selected = None

    with col1:
        if st.button("Quels sont les horaires de télétravail ?", use_container_width=True):
            selected = "Quels sont les horaires de télétravail ?"
        if st.button("Combien de jours de congés ?", use_container_width=True):
            selected = "Combien de jours de congés annuels ?"

    with col2:
        if st.button("Comment fonctionne la mutuelle ?", use_container_width=True):
            selected = "Comment fonctionne la mutuelle ?"
        if st.button("Quelle est l'architecture technique ?", use_container_width=True):
            selected = "Quelle est l'architecture technique du système ?"

    return selected


def render_footer():
    """Affiche le footer positionné proprement en bas"""
    