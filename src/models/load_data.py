import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def load_stocks(data_path: Path = Path("data/raw")) -> pd.DataFrame:
    files = sorted(data_path.glob("stocks_*.parquet"))
    if not files:
        raise FileNotFoundError(f"nenhum parquet foi encontrado {data_path}")
    df = pd.concat([pd.read_parquet(f) for f in files])

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    df["daily_return"] = df.groupby(["ticker"])["close"].pct_change()

    df["log_return"] = df.groupby("ticker")["close"].transform(
        lambda x: np.log(x / x.shift(1))
    )

    df["realized_vol"] = df.groupby("ticker")["log_return"].transform(
        lambda x: x.rolling(5).std()
    )

    logger.info("Dados carregados %s", df.shape)
    return df.dropna(subset=["log_return", "realized_vol"])
