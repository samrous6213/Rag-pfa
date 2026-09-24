"""
Test complet du pipeline RAG
1. Ingestion des documents
2. Recherche dans Qdrant
3. Génération avec Ollama
"""

import requests
import json
from sentence_transformers import SentenceTransformer

QDRANT_URL = 'http://localhost:6333'
OLLAMA_URL = 'http://localhost:11434'
COLLECTION = 'documents'
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'


def test_ingestion():
    """Vérifie que les documents sont dans Qdrant"""
    print("\n" + "=" * 60)
    print("📊 TEST 1: Ingestion")
    print("=" * 60)

    response = requests.get(f'{QDRANT_URL}/collections/{COLLECTION}')
    data = response.json()

    points_count = data['result']['points_count']
    print(f"✅ {points_count} documents dans Qdrant")
    return points_count > 0


def test_search():
    """Test de recherche vectorielle"""
    print("\n" + "=" * 60)
    print("🔍 TEST 2: Recherche vectorielle")
    print("=" * 60)

    model = SentenceTransformer(EMBEDDING_MODEL)

    questions = [
        "Combien de jours de congés ?",
        "Quels sont les horaires de travail ?",
        "Comment fonctionne la mutuelle ?",
        "Quelle est l'architecture technique ?"
    ]

    for question in questions:
        print(f"\n❓ {question}")
        vector = model.encode(question).tolist()

        response = requests.post(
            f'{QDRANT_URL}/collections/{COLLECTION}/points/search',
            json={
                'vector': vector,
                'limit': 2,
                'with_payload': True
            }
        )

        results = response.json()['result']
        for i, r in enumerate(results):
            score = r['score']
            text = r['payload']['text'][:100].replace('\n', ' ')
            source = r['payload'].get('source', 'unknown')
            print(f"   [{i+1}] Score: {score:.3f} | {source} | {text}...")

    return True


def test_llm():
    """Test de génération avec Ollama"""
    print("\n" + "=" * 60)
    print("🤖 TEST 3: Génération LLM")
    print("=" * 60)

    prompt = """Tu es un assistant qui répond aux questions.

Question: Quelle est la capitale de la France ?
Réponse:"""

    response = requests.post(
        f'{OLLAMA_URL}/api/generate',
        json={
            'model': 'mistral',
            'prompt': prompt,
            'stream': False
        },
        timeout=120
    )

    result = response.json()
    answer = result.get('response', 'Pas de réponse')
    print(f"✅ Réponse: {answer[:200]}")
    return len(answer) > 0


def test_rag_pipeline():
    """Test complet RAG : recherche + génération"""
    print("\n" + "=" * 60)
    print("🎯 TEST 4: Pipeline RAG complet")
    print("=" * 60)

    model = SentenceTransformer(EMBEDDING_MODEL)

    question = "Combien de jours de congés annuels ?"
    print(f"\n❓ Question: {question}")

    vector = model.encode(question).tolist()
    response = requests.post(
        f'{QDRANT_URL}/collections/{COLLECTION}/points/search',
        json={'vector': vector, 'limit': 3, 'with_payload': True}
    )
    results = response.json()['result']

    if not results:
        print("❌ Aucun document trouvé")
        return False

    context = "\n\n".join([
        f"[{r['payload'].get('source', 'doc')}] {r['payload']['text']}"
        for r in results
    ])

    prompt = f"""Réponds à la question en te basant UNIQUEMENT sur le contexte.

CONTEXTE:
{context}

QUESTION: {question}

RÉPONSE:"""

    response = requests.post(
        f'{OLLAMA_URL}/api/generate',
        json={
            'model': 'mistral',
            'prompt': prompt,
            'stream': False
        },
        timeout=180
    )

    answer = response.json().get('response', 'Pas de réponse')
    print(f"\n✅ Réponse RAG: {answer}")
    return True


if __name__ == "__main__":
    print("\n" + "🧪" * 20)
    print("TEST COMPLET DU PIPELINE RAG")
    print("🧪" * 20)

    try:
        ok1 = test_ingestion()
        ok2 = test_search()
        ok3 = test_llm()
        ok4 = test_rag_pipeline()

        print("\n" + "=" * 60)
        if all([ok1, ok2, ok3, ok4]):
            print("✅ TOUS LES TESTS SONT PASSÉS !")
        else:
            print("⚠️ Certains tests ont échoué")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
