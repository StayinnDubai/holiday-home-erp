"""currencies

Revision ID: a7c2e9f4b6d1
Revises: f3b7e0a1c9d4
Create Date: 2026-08-12 00:00:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c2e9f4b6d1'
down_revision: Union[str, None] = 'f3b7e0a1c9d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CURRENCY_TABLE = sa.table(
    'currency',
    sa.column('id', sa.UUID()),
    sa.column('code', sa.String()),
    sa.column('name', sa.String()),
    sa.column('full_name', sa.String()),
    sa.column('is_deleted', sa.Boolean()),
)

CURRENCIES = [
    ('001', 'AED', 'UAE Dirham'),
    ('002', 'USD', 'US Dollar'),
    ('003', 'AMD', 'Armenian Dram'),
]


def upgrade() -> None:
    op.create_table(
        'currency',
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('name', sa.String(length=10), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_currency_code'), 'currency', ['code'], unique=True)

    op.bulk_insert(
        CURRENCY_TABLE,
        [{'id': uuid.uuid4(), 'code': code, 'name': name, 'full_name': full_name, 'is_deleted': False} for code, name, full_name in CURRENCIES],
    )

    # ---- bank_account.account_currency -> bank_account.currency_id ----
    op.add_column('bank_account', sa.Column('currency_id', sa.UUID(), nullable=True))
    op.execute(
        "UPDATE bank_account SET currency_id = (SELECT id FROM currency WHERE currency.name = bank_account.account_currency)"
    )
    op.execute(
        "UPDATE bank_account SET currency_id = (SELECT id FROM currency WHERE currency.name = 'AED') WHERE currency_id IS NULL"
    )
    op.alter_column('bank_account', 'currency_id', nullable=False)
    op.create_foreign_key(None, 'bank_account', 'currency', ['currency_id'], ['id'])
    op.drop_column('bank_account', 'account_currency')

    # ---- bank_statement_line.account_currency -> bank_statement_line.currency_id ----
    op.add_column('bank_statement_line', sa.Column('currency_id', sa.UUID(), nullable=True))
    op.execute(
        "UPDATE bank_statement_line SET currency_id = (SELECT id FROM currency WHERE currency.name = bank_statement_line.account_currency)"
    )
    op.execute(
        "UPDATE bank_statement_line SET currency_id = (SELECT id FROM currency WHERE currency.name = 'AED') WHERE currency_id IS NULL"
    )
    op.alter_column('bank_statement_line', 'currency_id', nullable=False)
    op.create_foreign_key(None, 'bank_statement_line', 'currency', ['currency_id'], ['id'])
    op.drop_column('bank_statement_line', 'account_currency')

    # ---- entity.base_currency -> entity.base_currency_id ----
    op.add_column('entity', sa.Column('base_currency_id', sa.UUID(), nullable=True))
    op.execute(
        "UPDATE entity SET base_currency_id = (SELECT id FROM currency WHERE currency.name = entity.base_currency)"
    )
    op.execute(
        "UPDATE entity SET base_currency_id = (SELECT id FROM currency WHERE currency.name = 'AED') WHERE base_currency_id IS NULL"
    )
    op.alter_column('entity', 'base_currency_id', nullable=False)
    op.create_foreign_key(None, 'entity', 'currency', ['base_currency_id'], ['id'])
    op.drop_column('entity', 'base_currency')


def downgrade() -> None:
    op.add_column('entity', sa.Column('base_currency', sa.String(length=3), nullable=True))
    op.execute("UPDATE entity SET base_currency = (SELECT name FROM currency WHERE currency.id = entity.base_currency_id)")
    op.alter_column('entity', 'base_currency', nullable=False)
    op.drop_constraint(None, 'entity', type_='foreignkey')
    op.drop_column('entity', 'base_currency_id')

    op.add_column('bank_statement_line', sa.Column('account_currency', sa.String(length=3), nullable=True))
    op.execute(
        "UPDATE bank_statement_line SET account_currency = (SELECT name FROM currency WHERE currency.id = bank_statement_line.currency_id)"
    )
    op.alter_column('bank_statement_line', 'account_currency', nullable=False)
    op.drop_constraint(None, 'bank_statement_line', type_='foreignkey')
    op.drop_column('bank_statement_line', 'currency_id')

    op.add_column('bank_account', sa.Column('account_currency', sa.String(length=3), nullable=True))
    op.execute(
        "UPDATE bank_account SET account_currency = (SELECT name FROM currency WHERE currency.id = bank_account.currency_id)"
    )
    op.alter_column('bank_account', 'account_currency', nullable=False)
    op.drop_constraint(None, 'bank_account', type_='foreignkey')
    op.drop_column('bank_account', 'currency_id')

    op.drop_index(op.f('ix_currency_code'), table_name='currency')
    op.drop_table('currency')
