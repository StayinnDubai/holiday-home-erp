"""counterparty group is_landlord_group flag

Revision ID: d2a4c6f8e1b3
Revises: efcf515466c7
Create Date: 2026-08-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2a4c6f8e1b3'
down_revision: Union[str, None] = 'efcf515466c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'counterparty_group',
        sa.Column('is_landlord_group', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('counterparty_group', 'is_landlord_group', server_default=None)


def downgrade() -> None:
    op.drop_column('counterparty_group', 'is_landlord_group')
