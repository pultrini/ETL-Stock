"""create_stocks_and_cypto_tables

Revision ID: 9444256ce560
Revises: 
Create Date: 2026-03-19 16:30:19.849977

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9444256ce560'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stocks_ohlcv",
        sa.Column("id",         sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ticker",     sa.String(20),  nullable=False),
        sa.Column("date",       sa.Date,        nullable=False),
        sa.Column("open",       sa.Numeric(18, 6)),
        sa.Column("high",       sa.Numeric(18, 6)),
        sa.Column("low",        sa.Numeric(18, 6)),
        sa.Column("close",      sa.Numeric(18, 6)),
        sa.Column("volume",     sa.BigInteger),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("ticker", "date", name="uq_stocks_ticker_date"),
    )

    op.create_table(
        "crypto_ohlcv",
        sa.Column("id",         sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("coin_id",    sa.String(50),  nullable=False),
        sa.Column("ticker",     sa.String(20),  nullable=False),
        sa.Column("date",       sa.Date,        nullable=False),
        sa.Column("open",       sa.Numeric(24, 8)),
        sa.Column("high",       sa.Numeric(24, 8)),
        sa.Column("low",        sa.Numeric(24, 8)),
        sa.Column("close",      sa.Numeric(24, 8)),
        sa.Column("volume",     sa.Numeric(30, 2)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("coin_id", "date", name="uq_crypto_coin_date"),
    )

    # índices para queries por período — padrão em dados financeiros
    op.create_index("ix_stocks_ticker_date", "stocks_ohlcv", ["ticker", "date"])
    op.create_index("ix_crypto_coin_date",   "crypto_ohlcv", ["coin_id", "date"])


def downgrade() -> None:
    op.drop_index("ix_crypto_coin_date",   table_name="crypto_ohlcv")
    op.drop_index("ix_stocks_ticker_date", table_name="stocks_ohlcv")
    op.drop_table("crypto_ohlcv")
    op.drop_table("stocks_ohlcv")
