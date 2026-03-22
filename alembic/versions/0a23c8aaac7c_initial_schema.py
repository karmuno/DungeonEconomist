"""initial schema

Revision ID: 0a23c8aaac7c
Revises:
Create Date: 2026-03-22 14:28:24.186608

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0a23c8aaac7c'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Tables with no FK dependencies ---
    op.create_table('accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('dungeon_nodes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('difficulty', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

    # --- keeps depends on accounts ---
    op.create_table('keeps',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('treasury_gold', sa.Integer(), nullable=True),
    sa.Column('treasury_silver', sa.Integer(), nullable=True),
    sa.Column('treasury_copper', sa.Integer(), nullable=True),
    sa.Column('total_score', sa.Integer(), nullable=True),
    sa.Column('current_day', sa.Integer(), nullable=True),
    sa.Column('day_started_at', sa.DateTime(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('dungeon_name', sa.String(), nullable=True),
    sa.Column('max_dungeon_level', sa.Integer(), nullable=True),
    sa.Column('highest_level_achieved', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # --- parties <-> expeditions have a circular FK; create without cross-FK first ---
    op.create_table('parties',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('on_expedition', sa.Boolean(), nullable=True),
    sa.Column('current_expedition_id', sa.Integer(), nullable=True),
    sa.Column('keep_id', sa.Integer(), nullable=False),
    sa.Column('auto_delve_healed', sa.Boolean(), nullable=False),
    sa.Column('auto_delve_full', sa.Boolean(), nullable=False),
    sa.Column('auto_decide_events', sa.Boolean(), nullable=False),
    sa.Column('auto_delve_level', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['keep_id'], ['keeps.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('expeditions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('party_id', sa.Integer(), nullable=False),
    sa.Column('start_day', sa.Integer(), nullable=False),
    sa.Column('duration_days', sa.Integer(), nullable=True),
    sa.Column('return_day', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('finished_at', sa.DateTime(), nullable=True),
    sa.Column('dungeon_level', sa.Integer(), nullable=True),
    sa.Column('result', sa.String(), nullable=True),
    sa.Column('pending_event', sa.JSON(), nullable=True),
    sa.Column('resolved_phases', sa.Integer(), nullable=True),
    sa.Column('decision_day', sa.Integer(), nullable=True),
    sa.Column('simulation_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['party_id'], ['parties.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # Deferred cross-FK: parties.current_expedition_id -> expeditions.id
    op.create_foreign_key(
        'fk_parties_current_expedition_id',
        'parties', 'expeditions',
        ['current_expedition_id'], ['id'],
        ondelete='SET NULL',
    )

    # --- Tables depending on keeps, expeditions, dungeon_nodes ---
    op.create_table('expedition_node_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('expedition_id', sa.Integer(), nullable=False),
    sa.Column('node_id', sa.Integer(), nullable=False),
    sa.Column('success', sa.Boolean(), nullable=True),
    sa.Column('xp_earned', sa.Integer(), nullable=True),
    sa.Column('loot', sa.Integer(), nullable=True),
    sa.Column('log', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['expedition_id'], ['expeditions.id'], ),
    sa.ForeignKeyConstraint(['node_id'], ['dungeon_nodes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('adventurers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('keep_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('adventurer_class', sa.Enum('Fighter', 'Cleric', 'Magic-User', 'Elf', 'Dwarf', 'Hobbit', name='adventurerclass'), nullable=False),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.Column('xp', sa.Integer(), nullable=True),
    sa.Column('hp_current', sa.Integer(), nullable=True),
    sa.Column('hp_max', sa.Integer(), nullable=True),
    sa.Column('gold', sa.Integer(), nullable=True),
    sa.Column('silver', sa.Integer(), nullable=True),
    sa.Column('copper', sa.Integer(), nullable=True),
    sa.Column('is_available', sa.Boolean(), nullable=True),
    sa.Column('on_expedition', sa.Boolean(), nullable=True),
    sa.Column('is_assigned', sa.Boolean(), nullable=False),
    sa.Column('is_bankrupt', sa.Boolean(), nullable=False),
    sa.Column('is_dead', sa.Boolean(), nullable=False),
    sa.Column('death_day', sa.Integer(), nullable=True),
    sa.Column('death_party_name', sa.String(), nullable=True),
    sa.Column('bankruptcy_day', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['keep_id'], ['keeps.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # --- Tables depending on adventurers ---
    op.create_table('buildings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('keep_id', sa.Integer(), nullable=False),
    sa.Column('building_type', sa.String(), nullable=False),
    sa.Column('level', sa.Integer(), nullable=True),
    sa.Column('retired_adventurer_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['keep_id'], ['keeps.id'], ),
    sa.ForeignKeyConstraint(['retired_adventurer_id'], ['adventurers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('expedition_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('expedition_id', sa.Integer(), nullable=False),
    sa.Column('adventurer_id', sa.Integer(), nullable=False),
    sa.Column('xp_share', sa.Integer(), nullable=True),
    sa.Column('hp_change', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['adventurer_id'], ['adventurers.id'], ),
    sa.ForeignKeyConstraint(['expedition_id'], ['expeditions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('magic_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('adventurer_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('item_type', sa.String(), nullable=False),
    sa.Column('bonus', sa.Integer(), nullable=True),
    sa.Column('found_day', sa.Integer(), nullable=True),
    sa.Column('found_expedition_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['adventurer_id'], ['adventurers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # --- Association tables ---
    op.create_table('party_adventurer',
    sa.Column('party_id', sa.Integer(), nullable=False),
    sa.Column('adventurer_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['adventurer_id'], ['adventurers.id'], ),
    sa.ForeignKeyConstraint(['party_id'], ['parties.id'], ),
    sa.PrimaryKeyConstraint('party_id', 'adventurer_id')
    )
    op.create_table('building_assignments',
    sa.Column('building_id', sa.Integer(), nullable=False),
    sa.Column('adventurer_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['adventurer_id'], ['adventurers.id'], ),
    sa.ForeignKeyConstraint(['building_id'], ['buildings.id'], ),
    sa.PrimaryKeyConstraint('building_id', 'adventurer_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('building_assignments')
    op.drop_table('party_adventurer')
    op.drop_table('magic_items')
    op.drop_table('expedition_logs')
    op.drop_table('buildings')
    op.drop_table('adventurers')
    op.drop_table('expedition_node_results')
    # Drop deferred FK before dropping tables
    op.drop_constraint('fk_parties_current_expedition_id', 'parties', type_='foreignkey')
    op.drop_table('expeditions')
    op.drop_table('parties')
    op.drop_table('keeps')
    op.drop_table('dungeon_nodes')
    op.drop_table('accounts')
