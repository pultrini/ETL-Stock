import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from constants.constants import COINS

logger = logging.getLogger(__name__)

def extract_market_data(
    coins: dict[str, str] = COINS,
    period_days: int = 90,
) -> pd.DataFrame:
    """
    Extrai OHLCV de criptomoedas via yfinance.
    Mesmo padrão do stocks.py — facilita o transform unificado.
    """
    end = datetime.today()
    start = end - timedelta(days=period_days)

    frames: list[pd.DataFrame] = []

    for coin_id, ticker in coins.items():
        logger.info("Extraindo %s (%s)...", coin_id, ticker)
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
            raw["coin_id"] = coin_id
            raw["ticker"]  = ticker
            raw = raw[["coin_id", "ticker", "date", "open", "high", "low", "close", "volume"]]

            frames.append(raw)

        except Exception:
            logger.exception("Erro ao extrair %s", ticker)

    if not frames:
        raise RuntimeError("Nenhum dado de cripto extraído")

    result = pd.concat(frames, ignore_index=True)
    logger.info(
        "Extração cripto concluída: %d linhas, %d moedas",
        len(result),
        result["coin_id"].nunique(),
    )
    return result


def save_raw(df: pd.DataFrame, path: Path = Path("data/raw")) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = path / f"crypto_{timestamp}.parquet"
    df.to_parquet(output, index=False)
    logger.info("Salvo em %s", output)
    return output


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    df = extract_market_data()
    print(df.head(10))
    save_raw(df)
