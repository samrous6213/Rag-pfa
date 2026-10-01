# API REST - Plateforme RAG

Cette API REST, développée avec FastAPI et Python 3.10, permet d'interroger en langage naturel un corpus de documents PDF et TXT. Elle recherche les passages pertinents dans Qdrant, puis peut générer une réponse avec le modèle Mistral exécuté par Ollama.

L'API est exposée sur le port `8000` par le service Docker `api-rag`.

## Architecture

Le code de l'API est organisé en cinq modules Python :

- `main.py` : point d'entrée FastAPI et définition des routes.
- `config.py` : configuration centralisée à partir des variables d'environnement.
- `models.py` : schémas Pydantic des requêtes et des réponses.
- `services.py` : connexions à Qdrant, Ollama et Sentence Transformers.
- `rag.py` : logique RAG, de la recherche à la construction du prompt et à la génération.

La recherche vectorielle utilise la collection Qdrant `documents`. Les embeddings sont produits par Sentence Transformers avec `all-MiniLM-L6-v2` (384 dimensions). La génération de réponses s'appuie sur Mistral 7B via Ollama.

## Endpoints

Base URL locale : `http://localhost:8000`.

### `GET /`

Retourne le nom et la version de l'API, son état, ainsi que les chemins des endpoints disponibles.

```bash
curl http://localhost:8000/
```

```json
{
  "name": "RAG API - Assistant Documentaire",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "stats": "/stats",
    "query": "/query (POST)",
    "search": "/search (POST)"
  }
}
```

### `GET /health`

Vérifie la connexion à Qdrant et à Ollama. Le statut vaut `healthy` si les deux services répondent, et `degraded` dans le cas contraire. La réponse inclut également les modèles configurés et un horodatage.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "services": {
    "qdrant": "connected",
    "ollama": "connected",
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_model": "mistral"
  },
  "timestamp": "2026-09-28T12:00:00"
}
```

### `GET /stats`

Retourne le nombre de points dans la collection, son nom et les modèles configurés. Dans l'implémentation actuelle, `total_queries` et `avg_response_time` sont renvoyés à `0` et `0.0`.

```bash
curl http://localhost:8000/stats
```

```json
{
  "total_documents": 12,
  "total_queries": 0,
  "avg_response_time": 0.0,
  "collection_name": "documents",
  "embedding_model": "all-MiniLM-L6-v2",
  "llm_model": "mistral"
}
```

### `POST /query`

Pose une question au pipeline RAG. L'API recherche les passages pertinents, construit un contexte et demande une réponse à Mistral. Les sources peuvent être incluses dans la réponse.

Contraintes du corps :

- `question` : chaîne de 1 à 1 000 caractères, obligatoire.
- `top_k` : nombre de passages à rechercher, de 1 à 10 (défaut : `3`).
- `temperature` : température de génération entre `0.0` et `1.0` (défaut : `0.1`).
- `include_sources` : inclure les sources (défaut : `true`).

```bash
curl -X POST http://localhost:8000/query \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "Quels sont les horaires de télétravail ?",
    "top_k": 3,
    "temperature": 0.1,
    "include_sources": true
  }'
```

```json
{
  "answer": "Selon les documents, ...",
  "sources": [
    {
      "text": "...",
      "source": "politique_rh.pdf",
      "page": 1,
      "score": 0.82,
      "chunk_id": 0
    }
  ],
  "confidence": 0.78,
  "processing_time": 3.45,
  "model": "mistral",
  "timestamp": "2026-09-28T12:00:00"
}
```

La validation d'une requête invalide, par exemple une question vide ou un `top_k` hors limites, renvoie HTTP `422`.

### `POST /search`

Recherche les passages similaires sans appeler le LLM. Cet endpoint est utile pour explorer le corpus ou déboguer les résultats de recherche.

Contraintes du corps : `query` est obligatoire et contient de 1 à 1 000 caractères ; `top_k` est compris entre 1 et 20 (défaut : `5`).

```bash
curl -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "congés",
    "top_k": 5
  }'
```

```json
{
  "results": [
    {
      "text": "Extrait pertinent du document...",
      "source": "politique_rh.pdf",
      "page": 2,
      "score": 0.82
    }
  ],
  "total": 1,
  "query": "congés"
}
```

## Documentation interactive

- Swagger UI : [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc : [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Tests

La suite `scripts/test_api.py` comprend sept tests : vérification de l'état de santé, statistiques, requête RAG basique, requêtes multiples, recherche sans génération, validation des entrées invalides (HTTP `422`) et test anti-hallucination avec une question hors corpus.

Depuis la racine du projet, avec l'API accessible sur `http://localhost:8000`, lancez :

```bash
python scripts/test_api.py
```

## Configuration

Les valeurs par défaut ci-dessous sont celles définies par l'API. Dans le réseau Docker Compose, les hôtes Qdrant et Ollama sont respectivement `qdrant` et `ollama`.

| Variable | Défaut | Description |
| --- | --- | --- |
| `QDRANT_HOST` | `localhost` | Hôte de Qdrant (`qdrant` dans Docker Compose). |
| `QDRANT_PORT` | `6333` | Port de Qdrant. |
| `OLLAMA_HOST` | `localhost` | Hôte d'Ollama (`ollama` dans Docker Compose). |
| `OLLAMA_PORT` | `11434` | Port d'Ollama. |
| `OLLAMA_MODEL` | `mistral` | Modèle LLM utilisé pour la génération. |
| `COLLECTION_NAME` | `documents` | Nom de la collection Qdrant. |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Modèle Sentence Transformers utilisé pour les embeddings. |

## Prompt RAG et limitation des hallucinations

Le prompt système demande au LLM de répondre uniquement à partir du contexte récupéré, de ne pas inventer d'informations et de citer les sources lorsque c'est pertinent. Si l'information demandée n'apparaît pas dans le contexte, il doit indiquer : « Je ne trouve pas cette information dans les documents fournis. »