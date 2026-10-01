# Plateforme RAG

Plateforme de **Retrieval Augmented Generation (RAG)** développée dans le cadre d'un projet de fin d'année (PFA). Elle permet d'interroger en langage naturel un corpus documentaire hétérogène tout en garantissant la traçabilité des sources et la souveraineté des données.

Le projet fonctionne avec des composants exécutés localement : les documents, les embeddings, la recherche vectorielle et la génération par le LLM restent dans l'infrastructure du projet, sans appel à une API cloud externe.

## Problématique

> Comment concevoir et déployer une plateforme RAG capable de répondre en langage naturel à partir de documents PDF et TXT, tout en garantissant la traçabilité des sources et la souveraineté des données ?

## Objectifs

- Ingérer des documents hétérogènes, notamment PDF et TXT.
- Déposer les documents bruts dans un stockage objet MinIO.
- Découper les documents et générer leurs embeddings avec Sentence Transformers.
- Indexer les vecteurs et leurs métadonnées dans Qdrant.
- Utiliser un LLM local, Mistral 7B, via Ollama.
- Fournir des réponses accompagnées des sources utilisées.
- Orchestrer l'ingestion avec Apache Airflow.
- Déployer progressivement la plateforme avec Docker Compose puis Kubernetes sur Minikube.
- Évaluer la qualité du retrieval et de la génération avec RAGAS.

## Architecture

```text
Documents PDF / TXT déposés dans data/documents/
                         |
                         v
              DAG Apache Airflow (@daily)
                         |
                         v
          scripts/ingest.py : ingestion multi-format
              |                         |
              v                         v
 MinIO : documents-raw       LangChain : chargement et découpage
                                       |
                                       v
                    all-MiniLM-L6-v2 : embeddings 384 dim.
                                       |
                                       v
                         Qdrant : collection documents
                                       |
Question ---> Embedding ---> Recherche des passages pertinents
                                       |
                                       v
                         Contexte + métadonnées de source
                                       |
                                       v
                         Ollama / Mistral 7B local

Airflow Webserver : http://localhost:8080
Monitoring prévu : Langfuse
Évaluation prévue : RAGAS
Déploiement prévu : Kubernetes / Minikube
```

### Services Docker Compose

La stack complète contient six services :

| Service | Rôle | Accès local |
|---|---|---|
| `postgres` | Base PostgreSQL utilisée par Airflow | `localhost:5432` |
| `airflow-webserver` | Interface et serveur web Airflow | `http://localhost:8080` |
| `airflow-scheduler` | Exécution planifiée des DAGs | Interne à Docker |
| `qdrant` | Base de données vectorielle | `http://localhost:6333` |
| `minio` | Stockage objet compatible S3 | `http://localhost:9001` |
| `ollama` | Serveur local du LLM Mistral | `http://localhost:11434` |

Les services communiquent sur le réseau Docker `rag-network`. Le DAG utilise les noms DNS internes `qdrant`, `minio` et `ollama`, notamment `http://ollama:11434` pour Ollama. Cette organisation prépare le passage ultérieur à Kubernetes.

## Arborescence du projet

```text
rag/
├── dags/
│   └── rag_ingestion.py           # DAG Airflow d'ingestion
├── scripts/
│   ├── ingest.py                  # Ingestion PDF/TXT, MinIO et Qdrant
│   ├── test_search.py             # Test de recherche vectorielle
│   └── test_pipeline.py           # Test complet du pipeline RAG
├── api/                           # À venir : API FastAPI
├── ui/                            # À venir : interface Streamlit
├── k8s/                           # À venir : manifestes Kubernetes
├── data/
│   ├── documents/                 # Documents PDF et TXT à ingérer
│   ├── qdrant/                    # Données persistées de Qdrant
│   ├── minio/                     # Données persistées de MinIO
│   └── ollama/                    # Modèles Ollama
├── logs/                          # Logs Airflow, ignorés par Git
├── Dockerfile.airflow             # Image Airflow personnalisée
├── docker-compose.yml             # Stack complète des six services
├── docker-compose-minimal.yml     # Ancienne stack Qdrant + MinIO
├── requirements.txt               # Dépendances Python locales
├── .env                           # Variables d'environnement locales
├── .gitignore
└── README.md
```

Les documents de test utilisés pendant la Semaine 2 comprennent `test.txt`, `politique_rh.pdf` et `guide_tech.pdf`.

## Prérequis

L'environnement de développement utilisé est le suivant :

- macOS sur Apple Silicon ;
- Python 3.9 et un environnement virtuel (`venv`) ;
- Docker Desktop ;
- Homebrew ;
- Ollama exécuté dans Docker ;
- une connexion Internet initiale pour télécharger les images Docker, les dépendances et le modèle d'embedding ;
- le modèle Mistral disponible dans le volume Ollama.

Ports exposés par la stack complète :

| Service | Port | Usage |
|---|---:|---|
| PostgreSQL | `5432` | Backend Airflow |
| Airflow | `8080` | Interface web |
| Qdrant | `6333` | API HTTP |
| Qdrant | `6334` | API gRPC |
| MinIO | `9000` | API S3 |
| MinIO | `9001` | Console web |
| Ollama | `11434` | API locale du LLM |

## Installation

### 1. Installer Homebrew

Si la commande `brew` n'est pas disponible :

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Sur Apple Silicon, ajouter Homebrew au PATH :

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Vérifier l'installation :

```bash
brew --version
```

### 2. Préparer l'environnement Python local

Depuis la racine du projet :

```bash
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Versions principales utilisées :

```text
langchain==0.1.20
langchain-community==0.0.38
langchain-text-splitters==0.0.1
sentence-transformers==2.2.2
qdrant-client==1.6.4
pypdf==3.17.1
huggingface_hub==0.24.5
transformers==4.30.2
minio==7.2.0
reportlab
```

`reportlab` est utilisé pour générer des PDF de test. L'image Airflow personnalisée installe également les dépendances nécessaires à l'ingestion dans `Dockerfile.airflow`.

### 3. Préparer Mistral dans Ollama

Ollama est désormais exécuté dans le service Docker `ollama`, et non plus comme service natif installé via Homebrew. Démarrer d'abord la stack, puis télécharger Mistral dans le conteneur :

```bash
docker compose up -d ollama
docker exec -it ollama ollama pull mistral
```

Vérifier que le modèle est disponible :

```bash
docker exec -it ollama ollama list
```

Le modèle est conservé dans `data/ollama/`.

### 4. Construire l'image Airflow personnalisée

`Dockerfile.airflow` est basé sur `apache/airflow:2.7.1-python3.10` et installe les dépendances nécessaires directement dans l'image `rag-airflow:latest` :

```bash
docker build -f Dockerfile.airflow -t rag-airflow:latest .
```

Cette image évite l'installation des dépendances au démarrage et rend le lancement d'Airflow plus rapide et plus fiable.

## Démarrage des services

### Stack complète

Depuis la racine du projet :

```bash
docker compose up -d
```

Vérifier l'état des six services :

```bash
docker compose ps
```

Afficher les logs :

```bash
docker compose logs -f
```

L'interface Airflow est disponible sur <http://localhost:8080> avec les identifiants :

```text
Utilisateur : admin
Mot de passe : admin
```

La console MinIO est accessible sur <http://localhost:9001> avec les identifiants de développement : `minioadmin` / `minioadmin`.

Arrêter la stack :

```bash
docker compose down
```

Les données persistantes sont conservées dans `data/qdrant/`, `data/minio/` et `data/ollama/`. PostgreSQL utilise le volume Docker nommé `postgres_data`.

## DAG Airflow d'ingestion

Le fichier `dags/rag_ingestion.py` définit le DAG `rag_ingestion`, exécuté quotidiennement avec le schedule `@daily`. Il porte les tags `rag`, `ingestion` et `pfa`.

Les quatre tâches sont exécutées séquentiellement :

1. `check_services` vérifie l'accessibilité de Qdrant, MinIO et Ollama.
2. `run_ingestion` lance `scripts/ingest.py`.
3. `verify_indexation` vérifie la présence de points dans Qdrant et réalise une recherche de contrôle.
4. `cleanup_old_data` constitue le placeholder du futur nettoyage des anciennes données.

Pour lancer le DAG, ouvrir Airflow sur <http://localhost:8080>, rechercher `rag_ingestion`, puis l'activer et le déclencher depuis l'interface.

## Script d'ingestion

Le script `scripts/ingest.py` réalise les étapes suivantes :

1. Upload des fichiers PDF et TXT vers le bucket MinIO `documents-raw`.
2. Chargement des PDF avec `PyPDFLoader` et des TXT avec `TextLoader`.
3. Découpage avec `RecursiveCharacterTextSplitter` (`chunk_size=1000`, `chunk_overlap=200`).
4. Génération des embeddings avec `all-MiniLM-L6-v2` en 384 dimensions.
5. Recréation de la collection `documents` et insertion dans Qdrant.

Chaque point Qdrant contient notamment le texte, la source, la page, le `chunk_id` et la date `ingested_at`.

Pour exécuter l'ingestion directement depuis un conteneur Airflow :

```bash
docker exec airflow-webserver python /opt/airflow/scripts/ingest.py
```

Le déclenchement recommandé reste toutefois le DAG Airflow, afin de conserver l'orchestration et la vérification de l'indexation.

## Scripts de test

### Recherche vectorielle

`test_search.py` encode plusieurs questions avec `all-MiniLM-L6-v2`, interroge la collection `documents` et affiche les scores, les sources et les pages retournées :

```bash
python scripts/test_search.py
```

### Test complet du pipeline

`test_pipeline.py` vérifie successivement :

1. la présence des documents dans Qdrant ;
2. la recherche vectorielle sur plusieurs questions ;
3. la génération d'une réponse par Mistral via Ollama ;
4. le pipeline RAG complet, de la recherche au contexte puis à la génération.

Depuis l'hôte, avec Qdrant et Ollama exposés par Docker :

```bash
python scripts/test_pipeline.py
```

Le test complet du pipeline est validé pour l'ingestion, la recherche, le LLM et la génération RAG.

## Test de bout en bout

Le parcours Semaine 2 est le suivant :

```text
PDF / TXT
   -> upload MinIO
   -> chargement LangChain
   -> chunks de 1000 caractères avec overlap de 200
   -> embeddings all-MiniLM-L6-v2 (384 dimensions)
   -> indexation Qdrant
   -> recherche vectorielle
   -> contexte envoyé à Mistral via Ollama
   -> réponse RAG
```

Pour reproduire le pipeline :

```bash
source .venv/bin/activate
docker compose up -d
python scripts/ingest.py
python scripts/test_search.py
python scripts/test_pipeline.py
```

L'ingestion exécutée depuis l'hôte utilise les valeurs par défaut locales du script. Depuis Airflow, les services sont résolus avec les noms Docker `qdrant`, `minio` et `ollama`.

## Commandes utiles

| Action | Commande |
|---|---|
| Activer le venv | `source .venv/bin/activate` |
| Installer les dépendances locales | `pip install -r requirements.txt` |
| Construire l'image Airflow | `docker build -f Dockerfile.airflow -t rag-airflow:latest .` |
| Démarrer toute la stack | `docker compose up -d` |
| Voir l'état des services | `docker compose ps` |
| Voir tous les logs | `docker compose logs -f` |
| Voir les logs Airflow | `docker compose logs -f airflow-webserver airflow-scheduler` |
| Arrêter la stack | `docker compose down` |
| Démarrer Ollama seul | `docker compose up -d ollama` |
| Télécharger Mistral dans Ollama | `docker exec -it ollama ollama pull mistral` |
| Lister les modèles Ollama | `docker exec -it ollama ollama list` |
| Lancer l'ingestion | `python scripts/ingest.py` |
| Tester la recherche | `python scripts/test_search.py` |
| Tester le pipeline complet | `python scripts/test_pipeline.py` |
| Exécuter l'ingestion dans Airflow | `docker exec airflow-webserver python /opt/airflow/scripts/ingest.py` |
| Quitter le venv | `deactivate` |

## Problèmes rencontrés et solutions

### Conflit de dépendances LangChain

Les versions initiales `langchain==0.1.0` et `langchain-community==0.0.10` provoquaient des conflits. Les versions retenues sont :

```text
langchain==0.1.20
langchain-community==0.0.38
langchain-text-splitters==0.0.1
```

### `ImportError: cannot import name 'cached_download'`

L'erreur provenait d'une incompatibilité avec `huggingface_hub`. Elle a été résolue avec :

```bash
pip install "huggingface_hub==0.24.5" "transformers==4.30.2"
```

### PostgreSQL : `wrong ownership`

Le montage d'un répertoire local provoquait un problème de propriétaire avec PostgreSQL. La solution consiste à utiliser le volume Docker nommé `postgres_data` :

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

### Airflow plante au premier démarrage

L'installation des dépendances via `_PIP_ADDITIONAL_REQUIREMENTS` pouvait provoquer un timeout et ralentir le démarrage. La solution retenue est de construire l'image personnalisée `rag-airflow:latest` avec `Dockerfile.airflow`, les dépendances étant installées lors du build.

### `pull access denied for minio/minio`

L'image MinIO n'étant plus disponible à l'emplacement initial sur Docker Hub, la stack utilise :

```yaml
image: quay.io/minio/minio:latest
```

### Symlink Airflow suivi par Git

Le lien symbolique `logs/scheduler/latest` était suivi par Git. Il a été retiré du suivi et le répertoire `logs/` est ignoré par `.gitignore` afin de ne pas versionner les logs générés localement.

## Limites identifiées

Le test complet du pipeline passe pour l'ingestion, la recherche, la génération LLM et le pipeline RAG. Une limite a toutefois été identifiée pour la question « Quelle est l'architecture technique ? » : la recherche ne retrouve pas correctement `guide_tech.pdf`.

Deux facteurs expliquent ce résultat :

- `all-MiniLM-L6-v2` est limité pour la recherche en français technique ;
- le chunking regroupe le contenu de `guide_tech.pdf` en un seul chunk, ce qui dilue la spécificité recherchée.

Ces limites seront étudiées et mesurées pendant la phase d'évaluation RAGAS prévue en Semaine 6.

## État du projet

La Semaine 2 a ajouté la stack Docker Compose complète avec PostgreSQL, Airflow, Qdrant, MinIO et Ollama, ainsi que l'image Airflow personnalisée, l'ingestion PDF/TXT, le DAG quotidien et les tests de recherche et de pipeline RAG.

Le socle d'ingestion, d'indexation et de génération locale est opérationnel. L'API FastAPI, l'interface Streamlit et le déploiement Kubernetes sont encore à venir. L'évaluation RAGAS et l'analyse des limites de retrieval sont prévues pour la Semaine 6.

## Auteur

Projet de fin d'année (PFA) : **Plateforme RAG**

Auteur : **Sara Amrous**
