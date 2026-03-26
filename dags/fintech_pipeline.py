import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, str(Path("/opt/airflow")))

from constants.constants import DEFAULT_ARGS
from src.extract.crypto import extract_market_data
from src.extract.crypto import save_raw as save_raw_crypto
from src.extract.stocks import extract_ohlcv, save_raw
from src.load.supabase import load_crypto, load_stocks

logger = logging.getLogger(__name__)

default_args = {
    "owner": "fintech-etl",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

def task_extract_stocks(**context) -> str:
    """Extrai OHLCV de ações e salva em parquet. Retorna o path via XCom."""
    df = extract_ohlcv()
    output_path = save_raw(df, path=Path("/opt/airflow/data/raw"))
    logger.info("Stocks extraídos: %d linhas", len(df))

    return str(output_path)


def task_extract_crypto(**context) -> str:
    df = extract_market_data()
    output_path = save_raw_crypto(df, path=Path("/opt/airflow/data/raw"))
    logger.info("Crypto extraído: %d linhas", len(df))
    return str(output_path)



def task_check_data(**context) -> None:
    """
    Valida os arquivos gerados pelas tasks anteriores via XCom.
    Ponto de entrada para as validações de qualidade de dados.
    """
    ti = context["ti"]

    stocks_path = ti.xcom_pull(task_ids="extract_stocks")
    crypto_path = ti.xcom_pull(task_ids="extract_crypto")

    import pandas as pd

    for label, path in [("stocks", stocks_path), ("crypto", crypto_path)]:
        if not path or not Path(path).exists():
            raise FileNotFoundError(f"Arquivo {label} não encontrado: {path}")

        df = pd.read_parquet(path)

        if df.empty:
            raise ValueError(f"DataFrame {label} está vazio")

        if df.isna().all(axis=None):
            raise ValueError(f"DataFrame {label} só tem nulos")

        logger.info(
            "%s OK — shape: %s, nulos: %d",
            label,
            df.shape,
            df.isna().sum().sum(),
        )

def task_load_stocks(**context) -> None:
    ti = context["ti"]
    path = ti.xcom_pull(task_ids="extract_stocks")
    df = pd.read_parquet(path)
    inserted = load_stocks(df=df)
    logger.info("Success in load stocks in supabase, %d", inserted)


def task_load_crypto(**context) -> None:
    ti = context["ti"]
    path = ti.xcom_pull(task_ids="extract_crypto")
    df = pd.read_parquet(path)
    inserted = load_crypto(df=df)
    logger.info("Success in load crypto in supabase, %d", inserted)




with DAG(
    dag_id="fintech-etl",
    description="Extract provents and crypto data",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 1, 1),
    schedule="0 18 * * 1-5",
    catchup=False,
    tags=["fintech", "etl"],
):
    extract_stocks = PythonOperator(
        task_id="extract_stocks",
        python_callable=task_extract_stocks,
    )

    extract_crypto = PythonOperator(
        task_id="extract_crypto",
        python_callable=task_extract_crypto,
    )

    check_data = PythonOperator(
        task_id="check_data",
        python_callable=task_check_data,
    )

    load_crypto_task = PythonOperator(
        task_id="load_crypto_data",
        python_callable=task_load_crypto,
    )

    load_stocks_task = PythonOperator(
        task_id="load_stocks_data",
        python_callable=task_load_stocks,
    )

    extract_stocks >> load_stocks_task
    extract_crypto >> load_crypto_task

    [load_stocks_task, load_crypto_task] >> check_data
