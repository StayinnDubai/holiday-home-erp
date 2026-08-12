"""bank statement columns + bank_account_id link on bank_statement_line

Revision ID: d3f6b9c2e5a8
Revises: c9e1a5b8d3f6
Create Date: 2026-08-12 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3f6b9c2e5a8'
down_revision: Union[str, None] = 'c9e1a5b8d3f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BANK_STATEMENT_COLUMN_TABLE = sa.table(
    'bank_statement_column',
    sa.column('id', sa.UUID()),
    sa.column('column_key', sa.String()),
    sa.column('label', sa.String()),
    sa.column('visible', sa.Boolean()),
    sa.column('sort_order', sa.Integer()),
    sa.column('is_deleted', sa.Boolean()),
)

DEFAULT_COLUMNS = [
    ('bank_account_label', 'Bank account'),
    ('account_name', 'Account name'),
    ('account_type', 'Account type'),
    ('account_iban', 'Account IBAN'),
    ('account_number', 'Account number'),
    ('card_number', 'Card number'),
    ('currency_name', 'Account currency'),
    ('transaction_type', 'Transaction type'),
    ('date', 'Date'),
    ('ref_number', 'Ref. number'),
    ('description', 'Description'),
    ('amount', 'Amount (AED)'),
    ('balance', 'Balance (AED)'),
    ('original_ref_number', 'Original ref. number'),
    ('notes', 'Notes'),
]


def upgrade() -> None:
    op.add_column('bank_statement_line', sa.Column('bank_account_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'bank_statement_line', 'bank_account', ['bank_account_id'], ['id'])

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

    op.bulk_insert(
        BANK_STATEMENT_COLUMN_TABLE,
        [
            {'id': uuid.uuid4(), 'column_key': key, 'label': label, 'visible': True, 'sort_order': i, 'is_deleted': False}
            for i, (key, label) in enumerate(DEFAULT_COLUMNS)
        ],
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_bank_statement_column_key")
    op.drop_table('bank_statement_column')
    op.drop_constraint(None, 'bank_statement_line', type_='foreignkey')
    op.drop_column('bank_statement_line', 'bank_account_id')
