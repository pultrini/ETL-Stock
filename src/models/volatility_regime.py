import logging
import warnings

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from scipy import stats
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


def fit_hmm(df: pd.DataFrame, ticker: str, n_regimes: int = 3) -> dict:
    data = df[df["ticker"] == ticker].copy()

    if len(data) < 30:
        raise ValueError(f"{ticker}: dados insuficientes ({len(data)} linhas)")

    n_regimes = min(n_regimes, len(data) // 20)

    features = data[["log_return", "realized_vol"]].values
    scaler = StandardScaler()
    X = scaler.fit_transform(features)

    model = GaussianHMM(
        n_components=n_regimes,
        covariance_type="full",
        n_iter=1000,
        random_state=42,
        tol=1e-4,
    )
    model.fit(X)

    regimes = model.predict(X)
    data = data.copy()
    data["regime"] = regimes

    vol_by_regime = data.groupby("regime")["realized_vol"].mean().sort_values()
    regime_map = {old: new for new, old in enumerate(vol_by_regime.index)}
    data["regime"] = data["regime"].map(regime_map)

    logger.info("HMM ajustado para %s - log-likelihood: %.2f", ticker, model.score(X))

    return {
        "model": model,
        "data": data,
        "scaler": scaler,
        "ticker": ticker,
        "n_regimes": n_regimes,
    }


def compute_metrics_risk(returns: np.ndarray, confidence: float = 0.95) -> dict:
    clean = returns[~np.isnan(returns)]

    if len(clean) < 5:
        logger.warning(
            "Regime com apenas %d observações — métricas serão NaN", len(clean)
        )
        return {
            "var_95_parametrico": np.nan,
            "var_95_historico": np.nan,
            "cvar_95": np.nan,
            "sharpe_anualizado": np.nan,
            "max_drawdown": np.nan,
            "media_retorno": np.nan,
            "volatilidade": np.nan,
            "n_observacoes": len(clean),
        }

    mu, sigma = clean.mean(), clean.std()

    var_param = -(mu + stats.norm.ppf(1 - confidence) * sigma)
    var_hist = -np.percentile(clean, (1 - confidence) * 100)

    # bug fix: comparar com -var_hist (cauda negativa)
    tail = clean[clean <= -var_hist]
    cvar = -tail.mean() if len(tail) > 0 else np.nan

    sharpe = (mu / sigma) * np.sqrt(252) if sigma > 0 else np.nan

    cumulative = (1 + clean).cumprod()
    rolling_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - rolling_max) / rolling_max
    max_dd = drawdown.min()

    return {
        "var_95_parametrico": round(var_param, 6),
        "var_95_historico": round(var_hist, 6),
        "cvar_95": round(float(cvar), 6) if not np.isnan(cvar) else np.nan,
        "sharpe_anualizado": round(sharpe, 4),
        "max_drawdown": round(max_dd, 6),
        "media_retorno": round(mu, 6),
        "volatilidade": round(sigma, 6),
        "n_observacoes": len(clean),
    }


def risk_by_regime(result: dict, confidence: float = 0.95) -> pd.DataFrame:
    data = result["data"]
    total = len(data)
    rows = []

    regime_labels = {0: "Baixa Vol", 1: "Média Vol", 2: "Alta Vol"}

    for regime in sorted(data["regime"].unique()):
        subset = data[data["regime"] == regime]["daily_return"].values
        metrics = compute_metrics_risk(subset, confidence)

        # bug fix: pct_tempo estava faltando
        metrics["regime"] = regime
        metrics["regime_nome"] = regime_labels.get(regime, f"Regime {regime}")
        metrics["pct_tempo"] = round(len(subset) / total * 100, 1)

        rows.append(metrics)

    return pd.DataFrame(rows).set_index("regime")


def stress_test(result: dict) -> pd.DataFrame:
    data = result["data"].copy()
    returns = data["daily_return"].dropna().values

    baseline_var = compute_metrics_risk(returns)["var_95_historico"]

    scenarios = {
        "Crash -20% (5 dias)": np.append(returns, [-0.04] * 5),
        "Crise de liquidez": np.random.normal(
            returns.mean(), returns.std() * 3, size=len(returns)
        ),
        "Alta vol sustentada": np.append(
            returns, np.random.normal(0, np.percentile(np.abs(returns), 95), size=30)
        ),
    }

    rows = []
    for name, scenario_returns in scenarios.items():
        metrics = compute_metrics_risk(scenario_returns)
        metrics["cenario"] = name
        metrics["impacto_var"] = (
            round((metrics["var_95_historico"] - baseline_var) / baseline_var * 100, 2)
            if not np.isnan(metrics["var_95_historico"])
            else np.nan
        )
        rows.append(metrics)

    return pd.DataFrame(rows).set_index("cenario")
