"""add is_assigned to adventurers and magic_items table

Revision ID: 481c6a5a3b94
Revises: 80fae7659954
Create Date: 2026-03-16 13:26:28.051962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


# revision identifiers, used by Alembic.
revision: str = '481c6a5a3b94'
down_revision: Union[str, Sequence[str], None] = '80fae7659954'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    existing = sa_inspect(conn).get_table_names()

    def has_column(table, column):
        cols = [c['name'] for c in sa_inspect(conn).get_columns(table)]
        return column in cols

    with op.batch_alter_table('adventurers', schema=None) as batch_op:
        if not has_column('adventurers', 'is_assigned'):
            batch_op.add_column(sa.Column('is_assigned', sa.Boolean(), server_default='0', nullable=False))

    if 'magic_items' not in existing:
        op.create_table(
            'magic_items',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('adventurer_id', sa.Integer(), sa.ForeignKey('adventurers.id'), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('item_type', sa.String(), nullable=False),
            sa.Column('found_day', sa.Integer(), nullable=True),
            sa.Column('found_expedition_id', sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    op.drop_table('magic_items')
    with op.batch_alter_table('adventurers', schema=None) as batch_op:
        batch_op.drop_column('is_assigned')
