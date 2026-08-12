"""bills, reconciliation matching, fx rates

Revision ID: e4d9a6c1f8b7
Revises: 7b1d4f9a2c6e
Create Date: 2026-08-13 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4d9a6c1f8b7'
down_revision: Union[str, None] = '7b1d4f9a2c6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bill',
        sa.Column('bill_number', sa.String(length=30), nullable=False),
        sa.Column('supplier_counterparty_id', sa.UUID(), nullable=False),
        sa.Column('unit_id', sa.UUID(), nullable=True),
        sa.Column('bill_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('contra_account_id', sa.UUID(), nullable=True),
        sa.Column('bank_account_id', sa.UUID(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['supplier_counterparty_id'], ['counterparty.id']),
        sa.ForeignKeyConstraint(['unit_id'], ['unit.id']),
        sa.ForeignKeyConstraint(['contra_account_id'], ['account.id']),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_account.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bill_bill_number'), 'bill', ['bill_number'], unique=True)

    op.add_column('cheque', sa.Column('matched_bank_statement_entry_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_cheque_matched_bank_statement_entry_id',
        'cheque',
        'bank_statement_entry',
        ['matched_bank_statement_entry_id'],
        ['id'],
    )

    op.add_column('bank_account_column', sa.Column('semantic_role', sa.String(length=20), nullable=True))

    op.add_column('currency', sa.Column('rate_to_base', sa.Numeric(precision=18, scale=6), nullable=True))


def downgrade() -> None:
    op.drop_column('currency', 'rate_to_base')

    op.drop_column('bank_account_column', 'semantic_role')

    op.drop_constraint('fk_cheque_matched_bank_statement_entry_id', 'cheque', type_='foreignkey')
    op.drop_column('cheque', 'matched_bank_statement_entry_id')

    op.drop_index(op.f('ix_bill_bill_number'), table_name='bill')
    op.drop_table('bill')
