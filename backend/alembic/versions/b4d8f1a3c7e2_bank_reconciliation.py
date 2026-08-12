"""bank reconciliation (custom columns per bank account)

Revision ID: b4d8f1a3c7e2
Revises: a7c2e9f4b6d1
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b4d8f1a3c7e2'
down_revision: Union[str, None] = 'a7c2e9f4b6d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bank_account_column',
        sa.Column('bank_account_id', sa.UUID(), nullable=False),
        sa.Column('key', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('data_type', sa.String(length=20), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_account.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bank_account_id', 'key', name='uq_bank_account_column_account_key'),
    )

    op.create_table(
        'bank_reconciliation_line',
        sa.Column('bank_account_id', sa.UUID(), nullable=False),
        sa.Column('values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_account.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('bank_reconciliation_line')
    op.drop_table('bank_account_column')
