# scripts/evaluate.py
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset

# Préparer les données de test
test_data = {
    "question": ["Quels sont les congés ?", "Comment demander un congé ?"],
    "answer": ["Les congés sont de 25 jours...", "Il faut remplir un formulaire..."],
    "contexts": [["Les congés annuels sont de 25 jours..."], ["Pour demander un congé..."]],
    "ground_truth": ["25 jours de congés annuels", "Remplir le formulaire RH-01"]
}

dataset = Dataset.from_dict(test_data)

# Évaluer
result = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)

print(result)