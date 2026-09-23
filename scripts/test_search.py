import os
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
COLLECTION_NAME = 'documents'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

client = QdrantClient(host=QDRANT_HOST, port=6333)
model = SentenceTransformer(EMBEDDING_MODEL)

questions = [
    "Combien de jours de congés payés ?",
    "Qui gère l'authentification ?",
    "Combien de formations par an ?",
    "Quel outil pour le stockage relationnel ?",
]

for q in questions:
    print(f"\n❓ {q}")
    vec = model.encode(q).tolist()
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=vec,
        limit=3,
    )
    for i, r in enumerate(results):
        src = r.payload.get('source', '?')
        page = r.payload.get('page', '?')
        text = r.payload['text'][:120].replace('\n', ' ')
        print(f"  [{i+1}] score={r.score:.3f} | {src} p.{page} | {text}...")
