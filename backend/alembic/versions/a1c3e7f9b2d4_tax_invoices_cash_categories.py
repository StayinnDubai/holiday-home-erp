"""tax codes, invoices, cash ledger, asset/cost categories

Revision ID: a1c3e7f9b2d4
Revises: e4d9a6c1f8b7
Create Date: 2026-08-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3e7f9b2d4'
down_revision: Union[str, None] = 'e4d9a6c1f8b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        'tax_code',
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rate', sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column('treatment', sa.String(length=20), nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=True),
        sa.Column('effective_to', sa.Date(), nullable=True),
        *_audit_columns(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tax_code_code'), 'tax_code', ['code'], unique=True)

    op.create_table(
        'asset_category',
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('useful_life_months', sa.Integer(), nullable=True),
        sa.Column('method', sa.String(length=20), nullable=False),
        sa.Column('residual_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_asset_category_code'), 'asset_category', ['code'], unique=True)

    op.create_table(
        'cost_type',
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('subtype', sa.String(length=100), nullable=True),
        sa.Column('direct_or_overhead', sa.String(length=20), nullable=False),
        sa.Column('recurring', sa.Boolean(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint('id'),
    )

    op.add_column('bill', sa.Column('tax_code_id', sa.UUID(), nullable=True))
    op.add_column('bill', sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0'))
    op.create_foreign_key('fk_bill_tax_code_id', 'bill', 'tax_code', ['tax_code_id'], ['id'])

    op.create_table(
        'invoice',
        sa.Column('invoice_number', sa.String(length=30), nullable=False),
        sa.Column('customer_counterparty_id', sa.UUID(), nullable=False),
        sa.Column('unit_id', sa.UUID(), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('tax_code_id', sa.UUID(), nullable=True),
        sa.Column('tax_amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('contra_account_id', sa.UUID(), nullable=True),
        sa.Column('bank_account_id', sa.UUID(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['customer_counterparty_id'], ['counterparty.id']),
        sa.ForeignKeyConstraint(['unit_id'], ['unit.id']),
        sa.ForeignKeyConstraint(['tax_code_id'], ['tax_code.id']),
        sa.ForeignKeyConstraint(['contra_account_id'], ['account.id']),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_account.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_invoice_invoice_number'), 'invoice', ['invoice_number'], unique=True)

    op.create_table(
        'cash_transaction',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('custodian_user_id', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('counterparty_id', sa.UUID(), nullable=True),
        sa.Column('reference', sa.String(length=255), nullable=True),
        sa.Column('contra_account_id', sa.UUID(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['counterparty_id'], ['counterparty.id']),
        sa.ForeignKeyConstraint(['contra_account_id'], ['account.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('cash_transaction')

    op.drop_index(op.f('ix_invoice_invoice_number'), table_name='invoice')
    op.drop_table('invoice')

    op.drop_constraint('fk_bill_tax_code_id', 'bill', type_='foreignkey')
    op.drop_column('bill', 'tax_amount')
    op.drop_column('bill', 'tax_code_id')

    op.drop_table('cost_type')

    op.drop_index(op.f('ix_asset_category_code'), table_name='asset_category')
    op.drop_table('asset_category')

    op.drop_index(op.f('ix_tax_code_code'), table_name='tax_code')
    op.drop_table('tax_code')
