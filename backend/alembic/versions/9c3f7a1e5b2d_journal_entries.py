"""journal entries

Revision ID: 9c3f7a1e5b2d
Revises: e8a4c1f7b2d9
Create Date: 2026-08-12 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c3f7a1e5b2d'
down_revision: Union[str, None] = 'e8a4c1f7b2d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'journal_entry',
        sa.Column('number', sa.String(length=30), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('period', sa.String(length=7), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('source_module', sa.String(length=30), nullable=False),
        sa.Column('memo', sa.String(length=500), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_journal_entry_number'), 'journal_entry', ['number'], unique=True)

    op.create_table(
        'journal_entry_line',
        sa.Column('journal_entry_id', sa.UUID(), nullable=False),
        sa.Column('account_id', sa.UUID(), nullable=False),
        sa.Column('unit_id', sa.UUID(), nullable=True),
        sa.Column('debit', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('credit', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['journal_entry_id'], ['journal_entry.id']),
        sa.ForeignKeyConstraint(['account_id'], ['account.id']),
        sa.ForeignKeyConstraint(['unit_id'], ['unit.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_journal_entry_line_journal_entry_id'), 'journal_entry_line', ['journal_entry_id'], unique=False
    )

    op.add_column('cheque', sa.Column('contra_account_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_cheque_contra_account_id_account', 'cheque', 'account', ['contra_account_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_cheque_contra_account_id_account', 'cheque', type_='foreignkey')
    op.drop_column('cheque', 'contra_account_id')

    op.drop_index(op.f('ix_journal_entry_line_journal_entry_id'), table_name='journal_entry_line')
    op.drop_table('journal_entry_line')

    op.drop_index(op.f('ix_journal_entry_number'), table_name='journal_entry')
    op.drop_table('journal_entry')
