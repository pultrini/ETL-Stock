import logging
from datetime import datetime, timedelta
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow")
from src.models.run import run
from constants.constants import TICKERS


logger = logging.getLogger(__name__)

default_args = {
    "owner": "model-runner",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def run_pipeline(**context) -> None:
    for ticker in TICKERS:
        try:
            run(ticker, n_regimes=4)
        except Exception as e:
            logger.error(e)

    logging.info("The model finished successfully")

with DAG(
    dag_id="model_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="0 21 * * 6",
    catchup=False,
    tags=["model", "hmm", "risk"],
):
    run_pipeline = PythonOperator(
        task_id="run_model",
        python_callable=run,
    )

    run_pipeline