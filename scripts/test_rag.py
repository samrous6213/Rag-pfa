"""
Test de la logique RAG
"""

import sys
import asyncio
sys.path.insert(0, 'api')

from rag import answer_question


async def main():
    questions = [
        "Quels sont les horaires de télétravail ?",
        "Combien de jours de congés annuels ?",
        "Comment fonctionne la mutuelle ?",
        "Quelle est la capitale de Mars ?"  # Question hors contexte
    ]

    for q in questions:
        print("\n" + "=" * 70)
        print(f"❓ {q}")
        print("=" * 70)

        result = await answer_question(q, top_k=3)

        print(f"\n💬 Réponse : {result['answer']}")
        print(f"\n📊 Confiance : {result['confidence']}")
        print(f"⏱️ Temps : {result['processing_time']}s")
        print(f"🤖 Modèle : {result['model']}")

        if result['sources']:
            print(f"\n📚 Sources ({len(result['sources'])}) :")
            for i, s in enumerate(result['sources'], 1):
                print(f"   [{i}] {s.source} (page {s.page}) - score: {s.score}")


if __name__ == "__main__":
    asyncio.run(main())
