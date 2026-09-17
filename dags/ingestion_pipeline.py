from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import sys

default_args = {
    'owner': 'etudiante',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def run_ingestion():
    """Lance le script d'ingestion"""
    result = subprocess.run(
        [sys.executable, '/opt/airflow/scripts/ingest.py'],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print(f"⚠️ Erreurs: {result.stderr}")
    if result.returncode != 0:
        raise Exception(f"Ingestion échouée: {result.stderr}")

dag = DAG(
    'rag_ingestion',
    default_args=default_args,
    description='Pipeline d\'ingestion RAG',
    schedule_interval='@daily',
    catchup=False,
    tags=['rag', 'ingestion', 'pfa']
)

ingest_task = PythonOperator(
    task_id='ingest_documents',
    python_callable=run_ingestion,
    dag=dag
)