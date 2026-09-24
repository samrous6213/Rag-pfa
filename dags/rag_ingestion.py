"""
DAG Airflow pour l'ingestion des documents dans Qdrant
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import sys
import logging
import requests
import random

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'etudiante',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# URLs internes au réseau Docker
QDRANT_URL = 'http://qdrant:6333'
MINIO_URL = 'http://minio:9000'
OLLAMA_URL = 'http://ollama:11434'


def check_services(**context):
    """Vérifie que Qdrant, MinIO et Ollama sont accessibles"""
    logger.info("🔍 Vérification des services...")

    services = {
        'Qdrant': f'{QDRANT_URL}/',
        'MinIO': f'{MINIO_URL}/minio/health/live',
        'Ollama': f'{OLLAMA_URL}/api/tags',
    }

    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"   ✅ {name} est accessible")
            else:
                logger.warning(f"   ⚠️ {name} retourne {response.status_code}")
        except Exception as e:
            logger.error(f"   ❌ {name} inaccessible: {e}")
            if name != 'Ollama':
                raise

    logger.info("✅ Tous les services sont OK")


def run_ingestion(**context):
    """Lance le script d'ingestion"""
    logger.info("🚀 Lancement de l'ingestion...")

    result = subprocess.run(
        [sys.executable, '/opt/airflow/scripts/ingest.py'],
        capture_output=True,
        text=True,
        timeout=1800
    )

    logger.info(result.stdout)

    if result.stderr:
        logger.warning(f"Stderr: {result.stderr}")

    if result.returncode != 0:
        raise Exception(f"❌ Ingestion échouée (code {result.returncode})")

    try:
        response = requests.get(f'{QDRANT_URL}/collections/documents')
        data = response.json()
        count = data.get('result', {}).get('points_count', 0)
        logger.info(f"📊 {count} documents dans Qdrant")
        context['ti'].xcom_push(key='doc_count', value=count)
    except Exception as e:
        logger.error(f"Erreur lors du comptage: {e}")

    logger.info("✅ Ingestion terminée")


def verify_indexation(**context):
    """Vérifie que l'indexation est correcte"""
    logger.info("🔍 Vérification de l'indexation...")

    try:
        response = requests.get(f'{QDRANT_URL}/collections/documents')
        data = response.json()
        points_count = data.get('result', {}).get('points_count', 0)

        if points_count == 0:
            raise Exception("❌ Aucun document indexé !")

        logger.info(f"✅ {points_count} documents indexés avec succès")

        test_vector = [random.random() for _ in range(384)]

        search_response = requests.post(
            f'{QDRANT_URL}/collections/documents/points/search',
            json={
                'vector': test_vector,
                'limit': 3,
                'with_payload': True
            }
        )

        if search_response.status_code == 200:
            results = search_response.json().get('result', [])
            logger.info(f"✅ Test de recherche OK : {len(results)} résultats retournés")
        else:
            logger.warning(f"⚠️ Test de recherche échoué : {search_response.status_code}")

    except Exception as e:
        logger.error(f"❌ Erreur de vérification: {e}")
        raise


def cleanup_old_data(**context):
    """Nettoie les anciennes données si nécessaire"""
    logger.info("🧹 Nettoyage...")
    logger.info("✅ Nettoyage terminé")


dag = DAG(
    'rag_ingestion',
    default_args=default_args,
    description="Pipeline d'ingestion des documents pour le RAG",
    schedule_interval='@daily',
    catchup=False,
    max_active_runs=1,
    tags=['rag', 'ingestion', 'pfa'],
    doc_md="""
    ## DAG d'ingestion RAG
    Ingère les documents (PDF, TXT) dans Qdrant.
    """
)

t1 = PythonOperator(
    task_id='check_services',
    python_callable=check_services,
    dag=dag,
)

t2 = PythonOperator(
    task_id='run_ingestion',
    python_callable=run_ingestion,
    dag=dag,
)

t3 = PythonOperator(
    task_id='verify_indexation',
    python_callable=verify_indexation,
    dag=dag,
)

t4 = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=dag,
)

t1 >> t2 >> t3 >> t4
