"""merge halfling rename heads

Revision ID: 660af69121d4
Revises: 112ac0985fc2, a71966cb4680
Create Date: 2026-03-25 11:43:59.527354

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '660af69121d4'
down_revision: str | Sequence[str] | None = ('112ac0985fc2', 'a71966cb4680')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
