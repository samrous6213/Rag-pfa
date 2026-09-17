# Plateforme RAG

Plateforme de **Retrieval Augmented Generation (RAG)** développée dans le cadre d'un projet de fin d'année (PFA). Elle permet d'interroger en langage naturel un corpus documentaire hétérogène tout en conservant la traçabilité des sources et la souveraineté des données.

Le projet est conçu pour fonctionner sans appel à une API cloud externe : les embeddings, la recherche vectorielle et la génération de réponses sont exécutés dans l'environnement local.

## Problématique

> Comment concevoir et déployer une plateforme RAG capable de répondre en langage naturel à partir de documents PDF, TXT et Word, tout en garantissant la traçabilité des sources et la souveraineté des données ?

## Objectifs

- Ingérer des documents hétérogènes : PDF, TXT et Word.
- Découper les documents et générer leurs embeddings.
- Indexer les vecteurs dans Qdrant.
- Utiliser un LLM local, Mistral 7B, via Ollama.
- Fournir des réponses accompagnées de citations des sources utilisées.
- Déployer la plateforme avec Docker Compose puis Kubernetes sur Minikube.
- Ajouter du monitoring avec Langfuse.
- Évaluer la qualité du retrieval et de la génération avec RAGAS.

## Architecture

```text
Documents (PDF / TXT / Word)
							|
							v
	 Ingestion LangChain + Airflow
							|
							+--> Stockage objet MinIO (S3-compatible)
							|
							v
 Sentence Transformers : all-MiniLM-L6-v2
							|
							v
			 Qdrant (base vectorielle)
							|
Question ---> Embedding ---> Recherche des passages pertinents
																			|
																			v
												 Contexte + sources documentaires
																			|
																			v
										 Mistral 7B local via Ollama
																			|
																			v
									API FastAPI ---> Interface Streamlit
																			|
																			v
									Réponse + citations des sources

Monitoring : Langfuse
Évaluation : RAGAS
Déploiement : Docker Compose puis Kubernetes / Minikube
```

Les composants sont exécutés localement afin de conserver les documents et les échanges dans l'infrastructure maîtrisée par le projet. Qdrant stocke les vecteurs et leurs métadonnées, tandis que MinIO fournit le stockage objet compatible S3.

## Arborescence du projet

```text
rag/
├── dags/                         # Pipelines Apache Airflow
├── scripts/                      # Scripts d'ingestion, d'évaluation et de test
├── api/                          # API FastAPI
├── ui/                           # Interface Streamlit
├── k8s/                          # Manifestes Kubernetes
├── data/
│   ├── documents/                # Documents à ingérer
│   ├── qdrant/                   # Données persistées de Qdrant
│   └── minio/                    # Données persistées de MinIO
├── docker-compose-minimal.yml    # Qdrant et MinIO pour le développement
├── docker-compose.yml            # Configuration Docker Compose complète
├── requirements.txt              # Dépendances Python
├── .env                          # Variables d'environnement locales
└── README.md
```

## Prérequis

L'environnement de développement utilisé est le suivant :

- macOS sur Apple Silicon ;
- Python 3.9 et un environnement virtuel (`venv`) ;
- Docker Desktop ;
- Homebrew ;
- Ollama avec le modèle Mistral téléchargé ;
- Qdrant et MinIO démarrés avec `docker-compose-minimal.yml`.

Les ports locaux utilisés sont :

| Service | Port | Usage |
|---|---:|---|
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

### 2. Installer et préparer Ollama

Ollama est installé sur l'environnement de développement. Pour l'installer avec Homebrew si nécessaire :

```bash
brew install --cask ollama
```

Télécharger le modèle local Mistral :

```bash
ollama pull mistral
```

Vérifier que le modèle est disponible :

```bash
ollama list
```

Ollama doit être lancé avant les appels de génération de l'API :

```bash
ollama serve
```

### 3. Créer l'environnement Python

Depuis la racine du projet :

```bash
python3.9 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Les versions utilisées pour le socle RAG sont notamment :

```text
langchain==0.1.20
langchain-community==0.0.38
langchain-text-splitters==0.0.1
sentence-transformers==2.2.2
qdrant-client==1.6.4
pypdf==3.17.1
huggingface_hub==0.24.5
transformers==4.30.2
```

## Démarrage des services

### Qdrant et MinIO

Le fichier minimal démarre les services nécessaires au test de recherche vectorielle :

```bash
docker compose -f docker-compose-minimal.yml up -d
```

Vérifier l'état des conteneurs :

```bash
docker compose -f docker-compose-minimal.yml ps
```

Les interfaces sont accessibles à l'adresse suivante :

- Qdrant : <http://localhost:6333>
- Console MinIO : <http://localhost:9001>
- Identifiants MinIO de développement : `minioadmin` / `minioadmin`

Arrêter les services :

```bash
docker compose -f docker-compose-minimal.yml down
```

Les données sont persistées dans `data/qdrant/` et `data/minio/`. Ne pas supprimer ces répertoires si les données locales doivent être conservées.

## Test de bout en bout

Le test actuellement validé suit le parcours : **document TXT → découpage en chunks → embeddings → Qdrant → recherche sémantique**.

Avec Qdrant démarré et l'environnement virtuel activé :

```bash
python scripts/test_e2e.py
```

Le script utilise le fichier `data/documents/test.txt`, génère les embeddings avec `all-MiniLM-L6-v2`, recrée la collection `test_documents`, insère les vecteurs puis exécute plusieurs questions de recherche.

La sortie attendue se termine par :

```text
============================================================
TEST TERMINE AVEC SUCCES !
============================================================
```

Ce test valide la recherche vectorielle. Il ne constitue pas encore un test complet de génération avec Mistral, ni une évaluation RAGAS.

## Tableau des commandes utiles

| Action | Commande |
|---|---|
| Activer le venv | `source .venv/bin/activate` |
| Installer les dépendances | `pip install -r requirements.txt` |
| Démarrer Qdrant et MinIO | `docker compose -f docker-compose-minimal.yml up -d` |
| Voir l'état des services | `docker compose -f docker-compose-minimal.yml ps` |
| Voir les logs des services | `docker compose -f docker-compose-minimal.yml logs -f` |
| Arrêter les services | `docker compose -f docker-compose-minimal.yml down` |
| Lister les modèles Ollama | `ollama list` |
| Télécharger Mistral | `ollama pull mistral` |
| Démarrer Ollama | `ollama serve` |
| Lancer le test E2E | `python scripts/test_e2e.py` |
| Quitter le venv | `deactivate` |

## Problèmes rencontrés et solutions

### `zsh: command not found: brew`

Homebrew n'était pas installé ou son chemin n'était pas chargé par zsh. Installer Homebrew puis ajouter son environnement à `~/.zprofile` :

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### `pull access denied for minio/minio`

L'image `minio/minio` ayant été retirée de Docker Hub, utiliser l'image publiée sur Quay.io :

```yaml
image: quay.io/minio/minio:latest
```

Cette configuration est déjà utilisée dans `docker-compose-minimal.yml`.

### Conflit de dépendances LangChain

Les premières versions `0.1.0` provoquaient un conflit entre LangChain et ses composants. Utiliser les versions compatibles suivantes :

```bash
pip install \
	"langchain==0.1.20" \
	"langchain-community==0.0.38" \
	"langchain-text-splitters==0.0.1"
```

### `ImportError: cannot import name 'cached_download'`

Cette erreur provenait d'une incompatibilité entre `sentence-transformers`, `huggingface_hub` et `transformers`. Réinstaller les versions utilisées par le projet :

```bash
pip install \
	"huggingface_hub==0.24.5" \
	"transformers==4.30.2"
```

## État du projet

Le socle local de recherche est opérationnel : Qdrant et MinIO démarrent avec Docker Compose, et le test document → embedding → Qdrant → recherche a été validé. L'architecture cible inclut également l'API FastAPI, l'interface Streamlit, Airflow, Ollama/Mistral, Langfuse, RAGAS et le déploiement Kubernetes décrit dans ce document.

## Auteur

Projet de fin d'année (PFA) : **Plateforme RAG**

Auteur : **à compléter**
