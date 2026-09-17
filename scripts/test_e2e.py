"""
Test de bout en bout : Document → Embedding → Qdrant → Recherche
"""

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Configuration
QDRANT_HOST = "localhost"
COLLECTION_NAME = "test_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def main():
    print("=" * 60)
    print("🧪 TEST DE BOUT EN BOUT")
    print("=" * 60)
    
    # 1. Charger le document
    print("\n📄 Étape 1: Chargement du document...")
    loader = TextLoader('data/documents/test.txt', encoding='utf-8')
    documents = loader.load()
    print(f"   ✅ Document chargé ({len(documents[0].page_content)} caractères)")
    
    # 2. Découper en chunks
    print("\n✂️ Étape 2: Découpage en chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    print(f"   ✅ {len(chunks)} chunks créés")
    for i, chunk in enumerate(chunks):
        print(f"      Chunk {i}: {chunk.page_content[:80]}...")
    
    # 3. Générer les embeddings
    print("\n🔢 Étape 3: Génération des embeddings...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [chunk.page_content for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    print(f"   ✅ {len(embeddings)} embeddings générés (dim: {embeddings.shape[1]})")
    
    # 4. Stocker dans Qdrant
    print("\n💾 Étape 4: Stockage dans Qdrant...")
    client = QdrantClient(host=QDRANT_HOST, port=6333)
    
    # Recréer la collection
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=embeddings.shape[1],
            distance=models.Distance.COSINE
        )
    )
    
    # Préparer les points
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            models.PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload={
                    'text': chunk.page_content,
                    'source': 'test.txt',
                    'chunk_id': i
                }
            )
        )
    
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"   ✅ {len(points)} vecteurs stockés")
    
    # 5. Tester la recherche
    print("\n🔍 Étape 5: Test de recherche...")
    questions = [
        "Combien de jours de télétravail par semaine ?",
        "Quels sont les horaires de travail ?",
        "Combien de jours de congés annuels ?",
        "Que faire en cas de maladie ?"
    ]
    
    for question in questions:
        print(f"\n   ❓ Question: {question}")
        query_vector = model.encode(question).tolist()
        results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=2
        )
        
        for i, r in enumerate(results):
            score = r.score
            text = r.payload['text'][:150].replace('\n', ' ')
            print(f"      [{i+1}] Score: {score:.3f} | {text}...")
    
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS !")
    print("=" * 60)

if __name__ == "__main__":
    main()
