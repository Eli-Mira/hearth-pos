"""Add tendered and change amounts to payments.

Revision ID: 1a4f0d0f7e21
Revises: 8797da4ce639
Create Date: 2026-09-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1a4f0d0f7e21"
down_revision: Union[str, None] = "8797da4ce639"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("payments") as batch_op:
        batch_op.add_column(
            sa.Column("tendered", sa.Numeric(10, 2), nullable=False, server_default="0.00")
        )
        batch_op.add_column(
            sa.Column("change", sa.Numeric(10, 2), nullable=False, server_default="0.00")
        )


def downgrade() -> None:
    with op.batch_alter_table("payments") as batch_op:
        batch_op.drop_column("change")
        batch_op.drop_column("tendered")
