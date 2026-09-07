"""add party disbanded flag

Disbanded parties are kept as rows so their expeditions stay in the history.

Revision ID: b3c9d1e2f4a5
Revises: 7ba61c4ee9ea
Create Date: 2026-09-06 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3c9d1e2f4a5'
down_revision: str | None = '7ba61c4ee9ea'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('parties', schema=None) as batch_op:
        batch_op.add_column(sa.Column('disbanded', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('parties', schema=None) as batch_op:
        batch_op.drop_column('disbanded')
