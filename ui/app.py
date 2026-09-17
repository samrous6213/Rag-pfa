"""
Interface utilisateur pour le RAG
"""

import streamlit as st
import httpx

st.set_page_config(
    page_title="📚 Assistant Documentaire",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Assistant Documentaire Intelligent")
st.markdown("Posez vos questions sur les documents d'entreprise")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    top_k = st.slider("Nombre de documents à récupérer", 1, 10, 3)
    st.markdown("---")
    st.markdown("### 📊 À propos")
    st.markdown("""
    Ce système utilise:
    - **Qdrant** pour la recherche vectorielle
    - **Mistral 7B** (local) pour la génération
    - **Sentence Transformers** pour les embeddings
    """)

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("📚 Sources"):
                for src in message["sources"]:
                    st.markdown(f"**{src['source']}** (page {src['page']})")
                    st.caption(src['text'][:300] + "...")

# Input
if question := st.chat_input("Posez votre question..."):
    # Ajouter la question
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    
    # Appel API
    with st.chat_message("assistant"):
        with st.spinner("🔍 Recherche dans les documents..."):
            try:
                response = httpx.post(
                    "http://api-rag:8000/query",
                    json={"question": question, "top_k": top_k},
                    timeout=60.0
                )
                data = response.json()
                
                st.markdown(data["answer"])
                st.caption(f"Confiance: {data['confidence']}")
                
                with st.expander("📚 Sources"):
                    for src in data["sources"]:
                        st.markdown(f"**{src['source']}** (page {src['page']})")
                        st.caption(src['text'][:300] + "...")
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": data["sources"]
                })
                
            except Exception as e:
                st.error(f"Erreur: {e}")