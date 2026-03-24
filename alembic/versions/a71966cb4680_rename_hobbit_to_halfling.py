"""rename hobbit to halfling

Revision ID: a71966cb4680
Revises: 552d7f354a91
Create Date: 2026-03-24 00:00:00.000000

"""
from alembic import op

# revision identifiers
revision = 'a71966cb4680'
down_revision = '552d7f354a91'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE adventurers SET adventurer_class = 'Halfling' WHERE adventurer_class = 'Hobbit'")


def downgrade() -> None:
    op.execute("UPDATE adventurers SET adventurer_class = 'Hobbit' WHERE adventurer_class = 'Halfling'")
