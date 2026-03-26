from datetime import timedelta

DEFAULT_ARGS = {
    "owner": "fintech-etl",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "PETR4.SA", "VALE3.SA"]
COINS = {
    "bitcoin":  "BTC-USD",
    "ethereum": "ETH-USD",
    "solana":   "SOL-USD",
    "cardano":  "ADA-USD",
}
