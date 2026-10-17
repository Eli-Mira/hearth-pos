"""Align persisted shift cash-reconciliation fields.

Revision ID: 4c8d2e09b351
Revises: 1a4f0d0f7e21
Create Date: 2026-09-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4c8d2e09b351"
down_revision: Union[str, None] = "1a4f0d0f7e21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("shifts") as batch_op:
        batch_op.alter_column("closing_float", new_column_name="opening_float")
        batch_op.add_column(sa.Column("variance", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("shifts") as batch_op:
        batch_op.drop_column("variance")
        batch_op.alter_column("opening_float", new_column_name="closing_float")
