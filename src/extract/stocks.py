import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from constants.constants import TICKERS

logger = logging.getLogger(__name__)



def extract_ohlcv(
    tickers: list[str] = TICKERS,
    period_days: int = 90,
) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=period_days)

    frames: list[pd.DataFrame] = []

    for ticker in tickers:
        logger.info("Extraindo %s...", ticker)
        try:
            raw = yf.download(
                ticker,
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                auto_adjust=True,
                progress=False,
            )

            if raw.empty:
                logger.warning("%s: sem dados retornados", ticker)
                continue

            raw.columns = raw.columns.get_level_values(0)
            raw = raw.reset_index()

            raw = raw.rename(columns={
                "Date":   "date",
                "Open":   "open",
                "High":   "high",
                "Low":    "low",
                "Close":  "close",
                "Volume": "volume",
            })
            raw["ticker"] = ticker
            raw = raw[["ticker", "date", "open", "high", "low", "close", "volume"]]

            frames.append(raw)

        except Exception:
            logger.exception("Erro ao extrair %s", ticker)

    if not frames:
        raise RuntimeError("Nenhum dado extraído")

    result = pd.concat(frames, ignore_index=True)
    logger.info(
        "Extração concluída: %d linhas, %d tickers",
        len(result),
        result["ticker"].nunique(),
    )
    return result


def save_raw(df: pd.DataFrame, path: Path = Path("data/raw")) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = path / f"stocks_{timestamp}.parquet"
    df.to_parquet(output, index=False)
    logger.info("Salvo em %s", output)
    return output
