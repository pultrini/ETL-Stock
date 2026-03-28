import logging
from pathlib import Path

from .load_data import load_stocks
from .visualization import plot_regimes, plot_risk_heatmap, plot_stress
from .volatility_regime import fit_hmm, risk_by_regime, stress_test

logger = logging.getLogger(__name__)


def run(ticker: str = "AAPL", n_regimes: int = 3) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    logger.info("=== Regime de volatilidade: %s ===", ticker)
    df = load_stocks()
    result = fit_hmm(df, ticker, n_regimes)

    risk_df = risk_by_regime(result)
    print(f"\n{'=' * 50}")
    print(f"RISCO POR REGIME — {ticker}")
    print(f"{'=' * 50}")
    print(
        risk_df[
            [
                "regime_nome",
                "pct_tempo",
                "var_95_historico",
                "cvar_95",
                "sharpe_anualizado",
                "max_drawdown",
            ]
        ].to_string()
    )

    # stress test
    stress_df = stress_test(result)
    print(f"\n{'=' * 50}")
    print(f"STRESS TEST — {ticker}")
    print(f"{'=' * 50}")
    print(
        stress_df[
            ["var_95_historico", "cvar_95", "max_drawdown", "impacto_var"]
        ].to_string()
    )

    # plots
    plot_regimes(result)
    plot_risk_heatmap(risk_df, ticker)
    plot_stress(stress_df, ticker)


if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "PETR4.SA", "VALE3.SA"]
    for t in tickers:
        try:
            run(ticker=t)
        except Exception:
            logger.exception("Erro ao processar %s", t)
