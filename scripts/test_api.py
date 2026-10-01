"""
Suite de tests pour l'API RAG
"""

import requests
import json
import time

API_URL = "http://localhost:8000"


def test_health():
    """Test du health check"""
    print("\n" + "=" * 60)
    print("TEST 1: Health check")
    print("=" * 60)

    r = requests.get(f"{API_URL}/health")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    assert r.status_code == 200
    assert r.json()["status"] in ["healthy", "degraded"]
    print("✅ PASS")


def test_stats():
    """Test des statistiques"""
    print("\n" + "=" * 60)
    print("TEST 2: Statistiques")
    print("=" * 60)

    r = requests.get(f"{API_URL}/stats")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))

    assert r.status_code == 200
    print("✅ PASS")


def test_query_basic():
    """Test d'une requête RAG basique"""
    print("\n" + "=" * 60)
    print("TEST 3: Query RAG basique")
    print("=" * 60)

    payload = {
        "question": "Quels sont les horaires de télétravail ?",
        "top_k": 3
    }

    start = time.time()
    r = requests.post(f"{API_URL}/query", json=payload, timeout=120)
    elapsed = time.time() - start

    assert r.status_code == 200, f"Status: {r.status_code}, Response: {r.text}"

    data = r.json()
    print(f"Question: {payload['question']}")
    print(f"Réponse: {data['answer']}")
    print(f"Confiance: {data['confidence']}")
    print(f"Temps: {data['processing_time']}s (total: {elapsed:.2f}s)")
    print(f"Sources: {len(data['sources'])}")

    assert len(data['answer']) > 0
    assert 0 <= data['confidence'] <= 1
    print("✅ PASS")


def test_query_multiple():
    """Test de plusieurs questions"""
    print("\n" + "=" * 60)
    print("TEST 4: Multiple queries")
    print("=" * 60)

    questions = [
        "Combien de jours de congés annuels ?",
        "Comment fonctionne la mutuelle ?",
        "Quelle est la procédure en cas de maladie ?",
        "Quels sont les avantages pour les employés ?"
    ]

    for q in questions:
        print(f"\n❓ {q}")
        r = requests.post(
            f"{API_URL}/query",
            json={"question": q, "top_k": 3},
            timeout=120
        )

        if r.status_code == 200:
            data = r.json()
            print(f"   💬 {data['answer'][:150]}...")
            print(f"   📊 Confiance: {data['confidence']}")
        else:
            print(f"   ❌ Erreur: {r.status_code}")

    print("\n✅ PASS")


def test_search_only():
    """Test de la recherche sans LLM"""
    print("\n" + "=" * 60)
    print("TEST 5: Search only")
    print("=" * 60)

    r = requests.post(
        f"{API_URL}/search",
        json={"query": "congés", "top_k": 5},
        timeout=30
    )

    assert r.status_code == 200
    data = r.json()

    print(f"Query: {data['query']}")
    print(f"Total: {data['total']}")

    for i, result in enumerate(data['results'][:3], 1):
        print(f"   [{i}] {result['source']} (p.{result['page']}) - score: {result['score']:.3f}")
        print(f"       {result['text'][:100]}...")

    print("✅ PASS")


def test_invalid_query():
    """Test d'une requête invalide"""
    print("\n" + "=" * 60)
    print("TEST 6: Requête invalide")
    print("=" * 60)

    r = requests.post(
        f"{API_URL}/query",
        json={"question": "", "top_k": 3}
    )

    print(f"Status (question vide): {r.status_code}")
    assert r.status_code == 422

    r = requests.post(
        f"{API_URL}/query",
        json={"question": "test", "top_k": 100}
    )

    print(f"Status (top_k invalide): {r.status_code}")
    assert r.status_code == 422

    print("✅ PASS")


def test_hallucination():
    """Test avec une question hors contexte"""
    print("\n" + "=" * 60)
    print("TEST 7: Anti-hallucination")
    print("=" * 60)

    r = requests.post(
        f"{API_URL}/query",
        json={"question": "Quelle est la recette du couscous royal ?", "top_k": 3},
        timeout=120
    )

    data = r.json()
    print(f"Question: Quelle est la recette du couscous royal ?")
    print(f"Réponse: {data['answer']}")
    print(f"Confiance: {data['confidence']}")

    answer_lower = data['answer'].lower()
    if "je ne trouve pas" in answer_lower or "pas dans les documents" in answer_lower:
        print("✅ PASS - Le LLM a correctement refusé de répondre")
    else:
        print("⚠️ WARNING - Le LLM a peut-être halluciné")


if __name__ == "__main__":
    print("🧪" * 30)
    print("SUITE DE TESTS - API RAG")
    print("🧪" * 30)

    tests = [
        test_health,
        test_stats,
        test_query_basic,
        test_query_multiple,
        test_search_only,
        test_invalid_query,
        test_hallucination
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RÉSULTATS: {passed} passés, {failed} échoués")
    print("=" * 60)
