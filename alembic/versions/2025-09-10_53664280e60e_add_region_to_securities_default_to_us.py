"""add region to securities, default to US

Revision ID: 53664280e60e
Revises: a90dbb2593fd
Create Date: 2025-09-10 14:12:19.896296
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "53664280e60e"
down_revision: Union[str, Sequence[str], None] = "a90dbb2593fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # keep the constraint change Alembic generated
    op.drop_constraint(
        op.f("uq_backtest_trade_signal_execution_strategy_per_run"),
        "backtest_trade",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_backtest_trade_signal_execution_strategy_per_run",
        "backtest_trade",
        ["run_id", "eod_signal_id", "execution_strategy_id"],
    )

    # 1) add column as nullable first
    op.add_column(
        "security",
        sa.Column("region", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    # 2) backfill existing rows
    op.execute("UPDATE security SET region = 'us' WHERE region IS NULL")

    # 3) enforce NOT NULL
    op.alter_column(
        "security",
        "region",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("security", "region")

    op.drop_constraint(
        "uq_backtest_trade_signal_execution_strategy_per_run",
        "backtest_trade",
        type_="unique",
    )
    op.create_unique_constraint(
        op.f("uq_backtest_trade_signal_execution_strategy_per_run"),
        "backtest_trade",
        ["run_id", "eod_signal_id", "signal_strategy_id", "execution_strategy_id"],
        postgresql_nulls_not_distinct=False,
    )
