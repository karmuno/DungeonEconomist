"""add player events

One player_events table plus the event_types lookup it points at, seeded with every id in
app.player_events.EventType. See buildplans/player-events-spec.md.

Revision ID: d5e1f2a3b4c6
Revises: c4d0e2f3a6b7
Create Date: 2026-09-12 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.player_events import EVENT_TYPE_DESCRIPTIONS

# revision identifiers, used by Alembic.
revision: str = 'd5e1f2a3b4c6'
down_revision: str | None = 'c4d0e2f3a6b7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    event_types = op.create_table(
        'event_types',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.bulk_insert(
        event_types,
        [{'id': event_type.value, 'description': description}
         for event_type, description in EVENT_TYPE_DESCRIPTIONS.items()],
    )

    op.create_table(
        'player_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('keep_id', sa.Integer(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_type_id'], ['event_types.id']),
        sa.ForeignKeyConstraint(['user_id'], ['accounts.id']),
        sa.ForeignKeyConstraint(['keep_id'], ['keeps.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_player_events_event_type_id', 'player_events', ['event_type_id'])
    op.create_index('ix_player_events_user_id', 'player_events', ['user_id'])
    op.create_index('ix_player_events_keep_id', 'player_events', ['keep_id'])
    op.create_index('ix_player_events_created_at', 'player_events', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_player_events_created_at', table_name='player_events')
    op.drop_index('ix_player_events_keep_id', table_name='player_events')
    op.drop_index('ix_player_events_user_id', table_name='player_events')
    op.drop_index('ix_player_events_event_type_id', table_name='player_events')
    op.drop_table('player_events')
    op.drop_table('event_types')
