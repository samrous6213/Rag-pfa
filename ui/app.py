"""
Interface Streamlit pour l'Assistant Documentaire RAG
"""

import streamlit as st
from datetime import datetime

from styles import CUSTOM_CSS
from utils import api_query, api_health, api_stats, api_search
from components import (
    render_header,
    render_user_message,
    render_assistant_message,
    render_sources,
    render_sidebar_stats,
    render_health_status,
    render_suggestions,
    render_footer
)

st.set_page_config(
    page_title="Assistant Documentaire RAG",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


with st.sidebar:
    st.markdown("## Configuration")

    top_k = st.slider(
        "Nombre de documents",
        min_value=1,
        max_value=10,
        value=3,
        help="Combien de passages récupérer dans la base"
    )

    temperature = st.slider(
        "Créativité du modèle",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        help="0 = déterministe, 1 = créatif"
    )

    st.markdown("---")

    st.markdown("## État des services")
    health = api_health()
    render_health_status(health)

    stats = api_stats()
    if stats:
        render_sidebar_stats(stats)

    st.markdown("---")

    st.markdown("## Actions")

    if st.button("Effacer la conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("Rafraîchir", use_container_width=True):
        st.rerun()

    st.markdown("---")

    st.markdown("""
    ### À propos

    Cet assistant utilise :
    - **Mistral 7B** (LLM local)
    - **Qdrant** (base vectorielle)
    - **Sentence Transformers** (embeddings)

    Toutes les données restent **locales**.
    """)


render_header()


chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        suggested = render_suggestions()
        if suggested:
            st.session_state.pending_question = suggested
            st.rerun()

    for message in st.session_state.messages:
        if message["role"] == "user":
            render_user_message(message["content"])
        else:
            render_assistant_message(
                answer=message["content"],
                confidence=message.get("confidence"),
                processing_time=message.get("processing_time"),
                model=message.get("model")
            )
            if message.get("sources"):
                render_sources(message["sources"])




if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
else:
    question = st.chat_input("Posez votre question...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.spinner("Recherche dans les documents et génération de la réponse..."):
        response = api_query(question, top_k=top_k, temperature=temperature)

    if response and "error" in response:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Erreur : {response['error']}"
        })
    elif response:
        st.session_state.messages.append({
            "role": "assistant",
            "content": response["answer"],
            "sources": response.get("sources", []),
            "confidence": response.get("confidence"),
            "processing_time": response.get("processing_time"),
            "model": response.get("model")
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Impossible d'obtenir une réponse"
        })

    st.rerun()


render_footer()