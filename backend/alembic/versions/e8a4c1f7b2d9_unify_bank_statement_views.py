"""unify bank statement original/reconciliation into one configurable model

Bank Statement - Original moves from a fixed schema (bank_statement_line) to the
same per-bank-account, fully-custom-column model Reconciliation already uses:
- bank_account_column gains `applies_to` ('original' | 'reconciliation') so the
  same Settings > Bank Account Columns designer drives both grids.
- bank_reconciliation_line is generalized into bank_statement_entry, gaining a
  `kind` discriminator for the same reason.
- bank_statement_line (fixed columns) and bank_statement_column (the global
  visibility toggle this superseded) are dropped outright -- both were introduced
  and retired within the same development pass, never shipped to real users.

Revision ID: e8a4c1f7b2d9
Revises: d3f6b9c2e5a8
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8a4c1f7b2d9'
down_revision: Union[str, None] = 'd3f6b9c2e5a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- bank_account_column: add applies_to, re-scope the unique index by it ----
    op.add_column(
        'bank_account_column',
        sa.Column('applies_to', sa.String(length=20), nullable=False, server_default='reconciliation'),
    )
    op.alter_column('bank_account_column', 'applies_to', server_default=None)
    op.execute("DROP INDEX uq_bank_account_column_account_key")
    op.execute(
        "CREATE UNIQUE INDEX uq_bank_account_column_account_key ON bank_account_column "
        "(bank_account_id, applies_to, key) WHERE is_deleted = false"
    )

    # ---- bank_reconciliation_line -> bank_statement_entry, gains kind ----
    op.rename_table('bank_reconciliation_line', 'bank_statement_entry')
    op.add_column(
        'bank_statement_entry',
        sa.Column('kind', sa.String(length=20), nullable=False, server_default='reconciliation'),
    )
    op.alter_column('bank_statement_entry', 'kind', server_default=None)

    # ---- retire the fixed-schema Original view and the global column toggle ----
    op.execute("DROP INDEX IF EXISTS uq_bank_statement_column_key")
    op.drop_table('bank_statement_column')
    op.drop_table('bank_statement_line')


def downgrade() -> None:
    op.create_table(
        'bank_statement_line',
        sa.Column('bank_account_id', sa.UUID(), nullable=True),
        sa.Column('account_name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.String(length=100), nullable=True),
        sa.Column('account_iban', sa.String(length=50), nullable=True),
        sa.Column('account_number', sa.String(length=50), nullable=True),
        sa.Column('card_number', sa.String(length=50), nullable=True),
        sa.Column('currency_id', sa.UUID(), nullable=False),
        sa.Column('transaction_type', sa.String(length=100), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('ref_number', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('balance', sa.Numeric(14, 2), nullable=True),
        sa.Column('original_ref_number', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_account.id']),
        sa.ForeignKeyConstraint(['currency_id'], ['currency.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'bank_statement_column',
        sa.Column('column_key', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('visible', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_bank_statement_column_key ON bank_statement_column (column_key) WHERE is_deleted = false"
    )

    op.drop_column('bank_statement_entry', 'kind')
    op.rename_table('bank_statement_entry', 'bank_reconciliation_line')

    op.execute("DROP INDEX uq_bank_account_column_account_key")
    op.execute(
        "CREATE UNIQUE INDEX uq_bank_account_column_account_key ON bank_account_column "
        "(bank_account_id, key) WHERE is_deleted = false"
    )
    op.drop_column('bank_account_column', 'applies_to')
