"""add strategy_id to EODSignals to match with strategy files

Revision ID: cbf5964bc08f
Revises: 5f0b84200f21
Create Date: 2025-08-13 13:37:55.566619
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cbf5964bc08f"
down_revision: Union[str, Sequence[str], None] = "5f0b84200f21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Add the column as nullable first so we can populate it
    op.add_column(
        "eod_signal",
        sa.Column("strategy_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    # 2) Populate existing rows
    op.execute(
        "UPDATE eod_signal SET strategy_id = 'sma_pullback_buy' WHERE strategy_id IS NULL"
    )

    # 3) Alter column to be NOT NULL
    op.alter_column("eod_signal", "strategy_id", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("eod_signal", "strategy_id")
