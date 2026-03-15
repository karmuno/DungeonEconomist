"""add buildings, dungeon fields, expedition interactive fields

Revision ID: 264e6d2e5d63
Revises: 734d0b72d556
Create Date: 2026-03-15 14:52:02.658336

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect


# revision identifiers, used by Alembic.
revision: str = '264e6d2e5d63'
down_revision: Union[str, Sequence[str], None] = '734d0b72d556'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # New tables (check if they already exist from create_tables())
    conn = op.get_bind()
    existing = sa_inspect(conn).get_table_names()

    if 'buildings' not in existing:
        op.create_table(
            'buildings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('keep_id', sa.Integer(), sa.ForeignKey('keeps.id'), nullable=False),
        sa.Column('building_type', sa.String(), nullable=False),
        sa.Column('level', sa.Integer(), server_default='1'),
        sa.Column('retired_adventurer_id', sa.Integer(), sa.ForeignKey('adventurers.id'), nullable=True),
    )

    if 'building_assignments' not in existing:
        op.create_table(
            'building_assignments',
            sa.Column('building_id', sa.Integer(), sa.ForeignKey('buildings.id'), primary_key=True),
            sa.Column('adventurer_id', sa.Integer(), sa.ForeignKey('adventurers.id'), primary_key=True),
        )

    # New columns on existing tables (check if already added by create_tables)
    def has_column(table, column):
        cols = [c['name'] for c in sa_inspect(conn).get_columns(table)]
        return column in cols
    with op.batch_alter_table('expeditions', schema=None) as batch_op:
        if not has_column('expeditions', 'dungeon_level'):
            batch_op.add_column(sa.Column('dungeon_level', sa.Integer(), nullable=True))
        if not has_column('expeditions', 'pending_event'):
            batch_op.add_column(sa.Column('pending_event', sa.JSON(), nullable=True))
        if not has_column('expeditions', 'resolved_phases'):
            batch_op.add_column(sa.Column('resolved_phases', sa.Integer(), nullable=True))

    with op.batch_alter_table('keeps', schema=None) as batch_op:
        if not has_column('keeps', 'dungeon_name'):
            batch_op.add_column(sa.Column('dungeon_name', sa.String(), nullable=True))
        if not has_column('keeps', 'max_dungeon_level'):
            batch_op.add_column(sa.Column('max_dungeon_level', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('keeps', schema=None) as batch_op:
        batch_op.drop_column('max_dungeon_level')
        batch_op.drop_column('dungeon_name')

    with op.batch_alter_table('expeditions', schema=None) as batch_op:
        batch_op.drop_column('resolved_phases')
        batch_op.drop_column('pending_event')
        batch_op.drop_column('dungeon_level')

    op.drop_table('building_assignments')
    op.drop_table('buildings')
