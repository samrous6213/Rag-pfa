# Interface utilisateur Streamlit

L’interface de la **Plateforme RAG** est un chat Streamlit permettant d’interroger le corpus documentaire en langage naturel. Elle consomme l’API FastAPI, qui réalise la recherche documentaire et transmet le contexte au modèle local Mistral 7B via Ollama. L’interface est accessible sur [http://localhost:8501](http://localhost:8501) lorsque le service est lancé.

## Architecture

Le code de l’interface est organisé en quatre modules Python :

- `app.py` : point d’entrée Streamlit. Définit la page, la barre latérale, le chat, la saisie des questions et le mode recherche. L’historique est conservé dans `st.session_state.messages`. Une soumission est traitée dans une seule exécution Streamlit, sans appel à `st.rerun()` après la réponse.
- `components.py` : composants d’affichage réutilisables pour l’en-tête, les messages, les sources, les suggestions, l’état des services et les statistiques de la barre latérale. Les contenus dynamiques injectés en HTML sont échappés.
- `styles.py` : thème CSS personnalisé injecté dans Streamlit. Il définit une présentation sobre, avec fond clair, texte neutre, bordures fines et police Inter. Les tailles de texte de la barre latérale sont ajustées selon le type d’élément.
- `utils.py` : appels HTTP à l’API (`/query`, `/health`, `/stats`, `/search`), export de conversation et helpers de présentation. Les requêtes distinguent les délais de connexion et de lecture ; `/query` utilise un délai de lecture de 600 secondes pour tenir compte de la génération sur CPU.

## Fonctionnalités

- **Chat interactif** : posez une question avec le champ de saisie en bas de page ou choisissez l’une des quatre suggestions. La question apparaît immédiatement ; un indicateur signale la génération, puis l’interface affiche la réponse, les sources et le score de confiance.
- **Indicateur de confiance** : le score entre 0 et 1 est présenté en pourcentage avec un libellé. Les niveaux sont Élevée (vert, à partir de 0,7), Moyenne (orange, à partir de 0,4) et Faible (rouge, sous 0,4).
- **Sources dépliables** : chaque source présente le fichier, la page, le `chunk_id`, un extrait et un score coloré.
- **Barre latérale** : configurez le nombre de passages récupérés (`top_k`, de 1 à 10) et la température (de 0,0 à 1,0). Elle indique l’état des services Qdrant et Ollama à partir de `/health`, les statistiques disponibles via `/stats` (documents et requêtes), et propose les actions pour effacer la conversation, rafraîchir l’interface ou exporter l’historique. Le bloc « À propos » rappelle les composants de la stack.
- **Recherche sans génération** : le mode recherche appelle `/search` et affiche les résultats bruts de Qdrant sans solliciter le LLM. Cette recherche est conçue pour fournir les résultats rapidement (généralement en moins d’une seconde).
- **Export Markdown** : dès qu’un message est présent, téléchargez la conversation sous forme de fichier Markdown. L’export inclut les questions, réponses, scores de confiance et sources.

## Configuration

La configuration Streamlit se trouve dans `ui/.streamlit/config.toml`. Elle fixe notamment le port `8501`, l’adresse d’écoute `0.0.0.0`, les couleurs du thème, CORS et la désactivation de la collecte des statistiques d’usage Streamlit. Les styles de l’interface, dont la police Inter, sont définis dans `styles.py`.

L’URL de l’API est définie par la variable d’environnement `API_URL` :

- Par défaut : `http://localhost:8000`.
- Dans le réseau Docker Compose : `http://api-rag:8000`.

## Lancement

### En local

Depuis la racine du projet :

```bash
cd ui
source ../venv/bin/activate
pip install -r requirements.txt
API_URL=http://localhost:8000 streamlit run app.py
```

L’interface est ensuite disponible sur [http://localhost:8501](http://localhost:8501). L’API doit être accessible à l’adresse indiquée par `API_URL`.

### Avec Docker Compose

Depuis la racine du projet, démarrez le service `ui-streamlit` :

```bash
docker-compose up -d ui-streamlit
docker-compose logs -f ui-streamlit
```

Le conteneur `ui-streamlit` expose l’interface sur le port `8501` et utilise `http://api-rag:8000` pour joindre l’API dans le réseau Docker Compose.

## Sécurité et gestion des erreurs

- Les messages et les contenus dynamiques issus du LLM ou des sources documentaires sont échappés avant leur injection dans le HTML, afin de prévenir les injections XSS via des documents indexés.
- Les réponses de l’API sont vérifiées : format JSON, champs attendus et bornes des scores affichés.
- Les erreurs de délai dépassé, de connexion, de statut HTTP 4xx/5xx et de format JSON invalide sont traitées séparément et signalées avec un message explicite dans l’interface.

## Captures d’écran

Les captures sont stockées dans [`docs/screenshots/`](../docs/screenshots/) :

- [01-accueil.png](../docs/screenshots/01-accueil.png) : page d’accueil et suggestions.
- [02-reponse.png](../docs/screenshots/02-reponse.png) : question et réponse avec l’indicateur de confiance.
- [03-sources.png](../docs/screenshots/03-sources.png) : sources dépliées.
- [04-sidebar.jpeg](../docs/screenshots/04-sidebar.jpeg) : barre latérale, statistiques et configuration.
- [05-recherche.png](../docs/screenshots/05-recherche.png) : mode recherche sans LLM.
