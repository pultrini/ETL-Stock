import logging
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
logger = logging.getLogger(__name__)


def _get_engine():
    url = os.environ["DATABASE_URL"]
    return create_engine(url, pool_pre_ping=True)


def _upsert(df: pd.DataFrame, table: str, conflict_cols: list[str]) -> int:
    """
    Generic Upsert Via INSERT
    ON CONFLICT DO NOTHING
    :return number of rows affected
    """
    engine = _get_engine()
    tmp = f"_tmp_{table}"
    with engine.connect() as conn:
        df.to_sql(tmp, con=conn, if_exists="replace", index=False)
        conflict = ", ".join(conflict_cols)
        cols = ", ".join(df.columns)

        result = conn.execute(
            text(f"""
            INSERT INTO {table} ({cols})
            SELECT {cols} FROM {tmp}
            ON CONFLICT ({conflict}) DO NOTHING
        """)
        )

        conn.execute(text(f"DROP TABLE {tmp}"))

    inserted = result.rowcount
    logger.info(f"Inserted {inserted} rows")
    return int(inserted)


def load_stocks(df: pd.DataFrame) -> int:
    cols = ["ticker", "date", "open", "high", "low", "close", "volume"]
    return _upsert(df[cols], "stocks_ohlcv", conflict_cols=["ticker", "date"])


def load_crypto(df: pd.DataFrame) -> int:
    cols = ["coin_id", "ticker", "date", "open", "high", "low", "close", "volume"]
    return _upsert(df[cols], "crypto_ohlcv", conflict_cols=["coin_id", "date"])
