"""Rename Hobbit to Halfling

Revision ID: 112ac0985fc2
Revises: 552d7f354a91
Create Date: 2026-03-23 08:52:56.503410

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '112ac0985fc2'
down_revision: str | Sequence[str] | None = '552d7f354a91'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename Hobbit class to Halfling in adventurers table."""
    op.execute("ALTER TYPE adventurerclass ADD VALUE IF NOT EXISTS 'Halfling'")
    op.execute("COMMIT")
    op.execute("UPDATE adventurers SET adventurer_class = 'Halfling' WHERE adventurer_class = 'Hobbit'")


def downgrade() -> None:
    """Revert Halfling back to Hobbit."""
    op.execute("UPDATE adventurers SET adventurer_class = 'Hobbit' WHERE adventurer_class = 'Halfling'")
