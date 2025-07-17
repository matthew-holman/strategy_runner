"""Add index constituent table

Revision ID: 3c60e1eb9e22
Revises: 
Create Date: 2025-07-17 15:16:28.765405

"""
from typing import Sequence, Union

import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c60e1eb9e22'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('indexconstituent',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('index_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('snapshot_date', sa.Date(), nullable=False),
    sa.Column('symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('company_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('gics_sector', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('gics_sub_industry', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('cik', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('date_added', sa.Date(), nullable=True),
    sa.Column('snapshot_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),

    sa.PrimaryKeyConstraint('id')
    )
    sa.UniqueConstraint("index_name", "snapshot_date", "symbol", name="uq_index_constituent_snapshot")

    op.create_index(op.f('ix_indexconstituent_cik'), 'indexconstituent', ['cik'], unique=False)
    op.create_index(op.f('ix_indexconstituent_index_name'), 'indexconstituent', ['index_name'], unique=False)
    op.create_index(op.f('ix_indexconstituent_snapshot_date'), 'indexconstituent', ['snapshot_date'], unique=False)
    op.create_index(op.f('ix_indexconstituent_snapshot_hash'), 'indexconstituent', ['snapshot_hash'], unique=False)
    op.create_index(op.f('ix_indexconstituent_symbol'), 'indexconstituent', ['symbol'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_indexconstituent_symbol'), table_name='indexconstituent')
    op.drop_index(op.f('ix_indexconstituent_snapshot_hash'), table_name='indexconstituent')
    op.drop_index(op.f('ix_indexconstituent_snapshot_date'), table_name='indexconstituent')
    op.drop_index(op.f('ix_indexconstituent_index_name'), table_name='indexconstituent')
    op.drop_index(op.f('ix_indexconstituent_cik'), table_name='indexconstituent')
    op.drop_table('indexconstituent')
    # ### end Alembic commands ###
