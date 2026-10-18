import os
from langfuse import get_client

langfuse = None

if os.getenv("LANGFUSE_PUBLIC_KEY"):
    # get_client() lit automatiquement les variables d'environnement
    langfuse = get_client()
    print("Langfuse initialisé")
else:
    print("Langfuse désactivé")