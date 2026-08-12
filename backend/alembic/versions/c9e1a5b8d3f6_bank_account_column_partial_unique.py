"""bank_account_column: partial unique index (ignore soft-deleted rows)

Revision ID: c9e1a5b8d3f6
Revises: b4d8f1a3c7e2
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c9e1a5b8d3f6'
down_revision: Union[str, None] = 'b4d8f1a3c7e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('uq_bank_account_column_account_key', 'bank_account_column', type_='unique')
    op.execute(
        "CREATE UNIQUE INDEX uq_bank_account_column_account_key ON bank_account_column "
        "(bank_account_id, key) WHERE is_deleted = false"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_bank_account_column_account_key")
    op.create_unique_constraint('uq_bank_account_column_account_key', 'bank_account_column', ['bank_account_id', 'key'])
