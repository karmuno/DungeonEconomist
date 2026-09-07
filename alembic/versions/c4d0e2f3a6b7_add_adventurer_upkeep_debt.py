"""add adventurer upkeep debt

Upkeep that came due while the adventurer was in the dungeon and could not be
paid is carried as a debt and settled when the expedition returns.

Revision ID: c4d0e2f3a6b7
Revises: b3c9d1e2f4a5
Create Date: 2026-09-07 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d0e2f3a6b7'
down_revision: str | None = 'b3c9d1e2f4a5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('adventurers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('upkeep_debt_cp', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('adventurers', schema=None) as batch_op:
        batch_op.drop_column('upkeep_debt_cp')
