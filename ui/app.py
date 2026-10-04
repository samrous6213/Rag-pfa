"""Interface Streamlit pour l'Assistant Documentaire RAG."""

from datetime import datetime

import streamlit as st

from components import (
    render_assistant_message,
    render_health_status,
    render_header,
    render_sidebar_stats,
    render_sources,
    render_suggestions,
    render_user_message,
)
from styles import CUSTOM_CSS
from utils import api_health, api_query, api_search, api_stats, export_conversation


st.set_page_config(
    page_title="Assistant Documentaire RAG",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("## Configuration")
    top_k = st.slider(
        "Nombre de documents",
        min_value=1,
        max_value=10,
        value=3,
        help="Combien de passages récupérer dans la base",
    )
    temperature = st.slider(
        "Créativité du modèle",
        min_value=0.0,
        max_value=1.0,
        value=0.1,
        step=0.1,
        help="0 = déterministe, 1 = créatif",
    )

    st.markdown("---")
    st.markdown("## État des services")
    render_health_status(api_health())

    stats = api_stats()
    if stats:
        render_sidebar_stats(stats)

    st.markdown("---")
    st.markdown("## Actions")
    if st.button("Effacer la conversation", use_container_width=True):
        st.session_state.messages = []

    st.button("Rafraîchir", use_container_width=True)

    export_placeholder = st.empty()
    if st.session_state.messages:
        export_placeholder.download_button(
            label="Exporter la conversation",
            data=export_conversation(st.session_state.messages),
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown(
        """
        ### À propos

        Cet assistant utilise :
        - **Mistral 7B** (LLM local)
        - **Qdrant** (base vectorielle)
        - **Sentence Transformers** (embeddings)

        Toutes les données restent **locales**.
        """
    )

render_header()

suggested_question = None
suggestions_placeholder = st.empty()
if not st.session_state.messages:
    with suggestions_placeholder.container():
        suggested_question = render_suggestions()

for message in st.session_state.messages:
    if message.get("role") == "user":
        render_user_message(message.get("content", ""))
    elif message.get("role") == "assistant":
        render_assistant_message(
            answer=message.get("content", ""),
            confidence=message.get("confidence"),
            processing_time=message.get("processing_time"),
            model=message.get("model"),
        )
        if message.get("sources"):
            render_sources(message["sources"])

chat_question = st.chat_input("Posez votre question...")
question = suggested_question or chat_question

if question:
    suggestions_placeholder.empty()
    st.session_state.messages.append({"role": "user", "content": question})
    render_user_message(question)

    with st.spinner("Recherche dans les documents et génération de la réponse..."):
        response = api_query(question, top_k=top_k, temperature=temperature)

    if response and "error" in response:
        assistant_message = {
            "role": "assistant",
            "content": f"Erreur : {response['error']}",
        }
    elif response:
        assistant_message = {
            "role": "assistant",
            "content": response["answer"],
            "sources": response.get("sources", []),
            "confidence": response.get("confidence"),
            "processing_time": response.get("processing_time"),
            "model": response.get("model"),
        }
    else:
        assistant_message = {
            "role": "assistant",
            "content": "Impossible d'obtenir une réponse.",
        }

    st.session_state.messages.append(assistant_message)
    export_placeholder.download_button(
        label="Exporter la conversation",
        data=export_conversation(st.session_state.messages),
        file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    render_assistant_message(
        answer=assistant_message["content"],
        confidence=assistant_message.get("confidence"),
        processing_time=assistant_message.get("processing_time"),
        model=assistant_message.get("model"),
    )
    if assistant_message.get("sources"):
        render_sources(assistant_message["sources"])

with st.expander("Mode recherche (sans LLM)"):
    st.markdown("Recherchez directement dans les documents sans génération LLM.")
    search_query = st.text_input("Rechercher...", key="search_input")
    search_k = st.slider("Nombre de résultats", 1, 20, 5, key="search_k")

    if st.button("Rechercher", key="search_btn"):
        if search_query.strip():
            with st.spinner("Recherche..."):
                results = api_search(search_query.strip(), search_k)

            if results and "error" not in results:
                result_items = results.get("results", [])
                st.success(f"{results.get('total', len(result_items))} résultats trouvés")
                for index, result in enumerate(result_items, 1):
                    if not isinstance(result, dict):
                        continue
                    st.markdown(f"**Résultat {index}**")
                    st.text(
                        f"{result.get('source', 'Inconnu')} "
                        f"(page {result.get('page', '?')}) — "
                        f"Score : {result.get('score', 0)}"
                    )
                    st.text(str(result.get("text", ""))[:300])
                    st.markdown("---")
            else:
                error = results.get("error", "Erreur inconnue") if results else "Erreur inconnue"
                st.error(f"Erreur : {error}")
        else:
            st.warning("Saisissez un terme à rechercher.")
