"""cheque bank account

Revision ID: 7b1d4f9a2c6e
Revises: 9c3f7a1e5b2d
Create Date: 2026-08-12 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b1d4f9a2c6e'
down_revision: Union[str, None] = '9c3f7a1e5b2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cheque', sa.Column('bank_account_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_cheque_bank_account_id_bank_account', 'cheque', 'bank_account', ['bank_account_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_cheque_bank_account_id_bank_account', 'cheque', type_='foreignkey')
    op.drop_column('cheque', 'bank_account_id')
