"""bank accounts

Revision ID: f3b7e0a1c9d4
Revises: d2a4c6f8e1b3
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3b7e0a1c9d4'
down_revision: Union[str, None] = 'd2a4c6f8e1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bank_account',
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('bank_id', sa.UUID(), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=True),
        sa.Column('account_iban', sa.String(length=50), nullable=True),
        sa.Column('account_number', sa.String(length=50), nullable=True),
        sa.Column('account_currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('open_date', sa.Date(), nullable=True),
        sa.Column('close_date', sa.Date(), nullable=True),
        sa.Column('chart_account_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['bank_id'], ['counterparty.id']),
        sa.ForeignKeyConstraint(['chart_account_id'], ['account.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bank_account_code'), 'bank_account', ['code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_bank_account_code'), table_name='bank_account')
    op.drop_table('bank_account')
