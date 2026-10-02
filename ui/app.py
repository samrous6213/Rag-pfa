"""
app.py - Interface Streamlit pour l'Assistant Documentaire RAG
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

    if st.session_state.messages:
        from utils import export_conversation
        md_content = export_conversation(st.session_state.messages)
        st.download_button(
            label="Exporter la conversation",
            data=md_content,
            file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True
        )

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
    # 1. Ajouter et afficher la question immédiatement
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })
    render_user_message(question)

    # 2. Spinner + appel API (la question reste visible au-dessus)
    with st.spinner("Recherche dans les documents et génération de la réponse..."):
        response = api_query(question, top_k=top_k, temperature=temperature)

    # 3. Ajouter la réponse à la session
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

    # 4. Rerun pour afficher proprement la réponse
    st.rerun()

# ===== MODE RECHERCHE =====
with st.expander("Mode recherche (sans LLM)"):
    st.markdown("Recherchez directement dans les documents sans génération LLM.")

    search_query = st.text_input("Rechercher...", key="search_input")
    search_k = st.slider("Nombre de résultats", 1, 20, 5, key="search_k")

    if st.button("Rechercher", key="search_btn"):
        if search_query:
            with st.spinner("Recherche..."):
                results = api_search(search_query, search_k)

            if results and "error" not in results:
                st.success(f"{results['total']} résultats trouvés")
                for i, r in enumerate(results["results"], 1):
                    st.markdown(f"""
**{i}. {r['source']}** (page {r['page']}) — Score : {r['score']:.3f}

{r['text'][:300]}...

---
""")
            else:
                st.error(f"Erreur : {results.get('error', 'Inconnue')}")

render_footer()