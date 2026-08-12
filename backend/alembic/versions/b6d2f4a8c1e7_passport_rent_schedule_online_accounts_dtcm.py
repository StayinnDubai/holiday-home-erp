"""passport/eid fields, rent auto-calc + adjustments, online accounts, dtcm permits

Revision ID: b6d2f4a8c1e7
Revises: a1c3e7f9b2d4
Create Date: 2026-08-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6d2f4a8c1e7'
down_revision: Union[str, None] = 'a1c3e7f9b2d4'
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
    # ---- Counterparty passport / Emirates ID fields ----
    op.add_column('counterparty', sa.Column('emirates_id_issue_date', sa.Date(), nullable=True))
    op.add_column('counterparty', sa.Column('emirates_id_expiry_date', sa.Date(), nullable=True))
    op.add_column('counterparty', sa.Column('nationality', sa.String(length=100), nullable=True))
    op.add_column('counterparty', sa.Column('passport_number', sa.String(length=50), nullable=True))
    op.add_column('counterparty', sa.Column('passport_issue_date', sa.Date(), nullable=True))
    op.add_column('counterparty', sa.Column('passport_expiry_date', sa.Date(), nullable=True))

    # ---- Tenancy contract rent auto-calculation toggle ----
    op.add_column('tenancy_contract', sa.Column('auto_calculate_rent', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('tenancy_contract', sa.Column('rent_schedule_generated', sa.Boolean(), nullable=False, server_default=sa.false()))

    # ---- Tenancy contract adjustments (discount / grace period / compensation) ----
    op.create_table(
        'tenancy_contract_adjustment',
        sa.Column('contract_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('discount_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['contract_id'], ['tenancy_contract.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ---- Bill traceability back to the tenancy contract that generated it ----
    op.add_column('bill', sa.Column('tenancy_contract_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_bill_tenancy_contract_id', 'bill', 'tenancy_contract', ['tenancy_contract_id'], ['id'])

    # ---- Online accounts (credential register) ----
    op.create_table(
        'online_account',
        sa.Column('service_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('related_to', sa.String(length=255), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('sign_in_method', sa.String(length=20), nullable=True),
        sa.Column('recovery_email', sa.String(length=255), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint('id'),
    )

    # ---- DTCM permits ----
    op.create_table(
        'dtcm_permit',
        sa.Column('permit_number', sa.String(length=50), nullable=False),
        sa.Column('unit_id', sa.UUID(), nullable=False),
        sa.Column('contract_id', sa.UUID(), nullable=True),
        sa.Column('dtcm_unit_unique_code', sa.String(length=50), nullable=True),
        sa.Column('operator_name', sa.String(length=255), nullable=True),
        sa.Column('operator_license_number', sa.String(length=50), nullable=True),
        sa.Column('operator_license_expiry_date', sa.Date(), nullable=True),
        sa.Column('operator_location', sa.String(length=255), nullable=True),
        sa.Column('operator_contact_details', sa.String(length=255), nullable=True),
        sa.Column('area', sa.String(length=255), nullable=True),
        sa.Column('unit_type', sa.String(length=50), nullable=True),
        sa.Column('building_name', sa.String(length=255), nullable=True),
        sa.Column('bedrooms', sa.Integer(), nullable=True),
        sa.Column('street_name', sa.String(length=255), nullable=True),
        sa.Column('unit_number', sa.String(length=50), nullable=True),
        sa.Column('street_number', sa.String(length=50), nullable=True),
        sa.Column('dewa_number', sa.String(length=100), nullable=True),
        sa.Column('lease_start_date', sa.Date(), nullable=True),
        sa.Column('lease_expiry_date', sa.Date(), nullable=True),
        sa.Column('plot_number', sa.String(length=50), nullable=True),
        sa.Column('unit_category', sa.String(length=50), nullable=True),
        sa.Column('issue_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('fee', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['unit_id'], ['unit.id']),
        sa.ForeignKeyConstraint(['contract_id'], ['tenancy_contract.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dtcm_permit_permit_number'), 'dtcm_permit', ['permit_number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_dtcm_permit_permit_number'), table_name='dtcm_permit')
    op.drop_table('dtcm_permit')

    op.drop_table('online_account')

    op.drop_constraint('fk_bill_tenancy_contract_id', 'bill', type_='foreignkey')
    op.drop_column('bill', 'tenancy_contract_id')

    op.drop_table('tenancy_contract_adjustment')

    op.drop_column('tenancy_contract', 'rent_schedule_generated')
    op.drop_column('tenancy_contract', 'auto_calculate_rent')

    op.drop_column('counterparty', 'passport_expiry_date')
    op.drop_column('counterparty', 'passport_issue_date')
    op.drop_column('counterparty', 'passport_number')
    op.drop_column('counterparty', 'nationality')
    op.drop_column('counterparty', 'emirates_id_expiry_date')
    op.drop_column('counterparty', 'emirates_id_issue_date')
