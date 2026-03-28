import logging
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

REGIME_COLORS = {0: "#2196F3", 1: "#FF9800", 2: "#F44336"}
REGIME_LABELS = {0: "Baixa Vol", 1: "Média Vol", 2: "Alta Vol"}
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


def plot_regimes(result: dict) -> None:
    data = result["data"]
    ticker = result["ticker"]

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(f"Regimes de Volatilidade — {ticker}", fontsize=14, fontweight="bold")

    ax1 = axes[0]
    ax1.plot(data["date"], data["close"], color="#333", linewidth=0.8, label="Preço")
    for regime, color in REGIME_COLORS.items():
        mask = data["regime"] == regime
        ax1.fill_between(
            data["date"],
            data["close"].min(),
            data["close"].max(),
            where=mask,
            alpha=0.15,
            color=color,
            label=REGIME_LABELS[regime],
        )
    ax1.set_ylabel("Preço (USD)")
    ax1.legend(loc="upper left", fontsize=8)

    ax2 = axes[1]
    for regime, color in REGIME_COLORS.items():
        mask = data["regime"] == regime
        ax2.scatter(
            data.loc[mask, "date"],
            data.loc[mask, "daily_return"],
            color=color,
            s=4,
            alpha=0.6,
            label=REGIME_LABELS[regime],
        )
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_ylabel("Retorno diário")

    ax3 = axes[2]
    ax3.plot(data["date"], data["realized_vol"], color="#555", linewidth=0.8)
    for regime, color in REGIME_COLORS.items():
        mask = data["regime"] == regime
        ax3.fill_between(
            data["date"],
            0,
            data["realized_vol"],
            where=mask,
            alpha=0.3,
            color=color,
        )
    ax3.set_ylabel("Volatilidade realizada (5d)")
    ax3.set_xlabel("Data")

    plt.tight_layout()
    plt.savefig(f"data/processed/{ticker}_regimes.png", dpi=150, bbox_inches="tight")
    plt.show()
    logger.info("Plot salvo: data/processed/%s_regimes.png", ticker)


def plot_risk_heatmap(risk_df: pd.DataFrame, ticker: str) -> None:
    cols = ["var_95_historico", "cvar_95", "max_drawdown", "sharpe_anualizado"]
    fig, ax = plt.subplots(figsize=(8, 3))
    sns.heatmap(
        risk_df[cols].astype(float),
        annot=True,
        fmt=".4f",
        cmap="RdYlGn_r",
        ax=ax,
        linewidths=0.5,
        yticklabels=risk_df["regime_nome"].values,
    )
    ax.set_title(f"Métricas de risco por regime — {ticker}")
    plt.tight_layout()
    plt.savefig(
        f"data/processed/{ticker}_risk_heatmap.png", dpi=150, bbox_inches="tight"
    )
    plt.show()


def plot_stress(stress_df: pd.DataFrame, ticker: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 4))
    x = range(len(stress_df))
    bars = ax.bar(x, stress_df["impacto_var"], color=["#F44336", "#FF9800", "#9C27B0"])
    ax.set_xticks(x)
    ax.set_xticklabels(stress_df.index, fontsize=9)
    ax.set_ylabel("Impacto no VaR 95% (%)")
    ax.set_title(f"Stress Test — Impacto no VaR — {ticker}")
    ax.axhline(0, color="black", linewidth=0.5)
    for bar, val in zip(bars, stress_df["impacto_var"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"+{val:.1f}%" if val > 0 else f"{val:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    plt.tight_layout()
    plt.savefig(f"data/processed/{ticker}_stress.png", dpi=150, bbox_inches="tight")
    plt.show()
