import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    keeps = relationship('Keep', back_populates='account')


class Keep(Base):
    """Merges the old Player + GameTime into a single per-game entity."""
    __tablename__ = 'keeps'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    name = Column(String, nullable=False)
    treasury_gold = Column(Integer, default=0)
    treasury_silver = Column(Integer, default=0)
    treasury_copper = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    current_day = Column(Integer, default=1)
    day_started_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    dungeon_name = Column(String, nullable=True)
    max_dungeon_level = Column(Integer, default=1)
    highest_level_achieved = Column(Integer, default=1)

    account = relationship('Account', back_populates='keeps')
    parties = relationship('Party', back_populates='keep')
    adventurers = relationship('Adventurer', back_populates='keep')
    buildings = relationship('Building', back_populates='keep')

    @property
    def treasury(self) -> int:
        """Legacy accessor: total treasury in gold pieces (floored)."""
        return self.treasury_total_copper() // 100

    def treasury_total_copper(self) -> int:
        """Convert all treasury currency to copper pieces."""
        return (self.treasury_gold * 100) + (self.treasury_silver * 10) + self.treasury_copper

    def add_treasury(self, copper_amount: int) -> None:
        """Add currency to treasury given as copper, distributing into gp/sp/cp."""
        total = self.treasury_total_copper() + copper_amount
        self.treasury_gold = total // 100
        self.treasury_silver = (total % 100) // 10
        self.treasury_copper = total % 10


class Building(Base):
    """A keep building that adventurers can be assigned to for bonuses."""
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True)
    keep_id = Column(Integer, ForeignKey('keeps.id'), nullable=False)
    building_type = Column(String, nullable=False)  # e.g. 'training_yard', 'shrine', etc.
    level = Column(Integer, default=1)
    retired_adventurer_id = Column(Integer, ForeignKey('adventurers.id'), nullable=True)

    keep = relationship('Keep', back_populates='buildings')
    retired_adventurer = relationship('Adventurer', foreign_keys=[retired_adventurer_id])
    assigned_adventurers = relationship(
        'Adventurer',
        secondary='building_assignments',
        back_populates='assigned_building',
    )


# Association table between Building and assigned Adventurers
building_assignments = Table(
    'building_assignments', Base.metadata,
    Column('building_id', Integer, ForeignKey('buildings.id'), primary_key=True),
    Column('adventurer_id', Integer, ForeignKey('adventurers.id'), primary_key=True),
)


# Association table between Party and Adventurer
party_adventurer = Table(
    'party_adventurer', Base.metadata,
    Column('party_id', Integer, ForeignKey('parties.id'), primary_key=True),
    Column('adventurer_id', Integer, ForeignKey('adventurers.id'), primary_key=True)
)


class AdventurerClass(enum.Enum):
    FIGHTER = 'Fighter'
    CLERIC = 'Cleric'
    MAGIC_USER = 'Magic-User'
    ELF = 'Elf'
    DWARF = 'Dwarf'
    HOBBIT = 'Hobbit'

class Adventurer(Base):
    __tablename__ = 'adventurers'

    id = Column(Integer, primary_key=True)
    keep_id = Column(Integer, ForeignKey('keeps.id'), nullable=False)
    name = Column(String, nullable=False)
    adventurer_class = Column(Enum(AdventurerClass, values_callable=lambda x: [e.value for e in x]), nullable=False)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    hp_current = Column(Integer, default=10)
    hp_max = Column(Integer, default=10)
    gold = Column(Integer, default=0)
    silver = Column(Integer, default=0)
    copper = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    on_expedition = Column(Boolean, default=False)
    is_assigned = Column(Boolean, default=False, nullable=False)
    is_bankrupt = Column(Boolean, default=False, nullable=False)
    is_dead = Column(Boolean, default=False, nullable=False)
    death_day = Column(Integer, nullable=True)
    death_party_name = Column(String, nullable=True)
    bankruptcy_day = Column(Integer, nullable=True)

    keep = relationship('Keep', back_populates='adventurers')
    parties = relationship('Party', secondary=party_adventurer, back_populates='members')
    expedition_logs = relationship('ExpeditionLog', back_populates='adventurer')
    assigned_building = relationship('Building', secondary='building_assignments', back_populates='assigned_adventurers')
    magic_items = relationship('MagicItem', back_populates='adventurer')

    def total_copper(self) -> int:
        """Convert all currency to copper pieces."""
        return (self.gold * 100) + (self.silver * 10) + self.copper

    def add_currency(self, copper_amount: int) -> None:
        """Add currency given as copper, distributing into gp/sp/cp."""
        total = self.total_copper() + copper_amount
        self.gold = total // 100
        self.silver = (total % 100) // 10
        self.copper = total % 10

    def subtract_currency(self, copper_amount: int) -> bool:
        """Subtract currency given as copper. Returns False if insufficient funds."""
        total = self.total_copper()
        if total < copper_amount:
            return False
        remaining = total - copper_amount
        self.gold = remaining // 100
        self.silver = (remaining % 100) // 10
        self.copper = remaining % 10
        return True

class Party(Base):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    name = Column(String, default='New Party')
    created_at = Column(DateTime)
    on_expedition = Column(Boolean, default=False)
    current_expedition_id = Column(Integer, ForeignKey('expeditions.id', ondelete='SET NULL'), nullable=True)
    keep_id = Column(Integer, ForeignKey('keeps.id'), nullable=False)
    auto_delve_healed = Column(Boolean, default=False, nullable=False)
    auto_delve_full = Column(Boolean, default=False, nullable=False)
    auto_decide_events = Column(Boolean, default=False, nullable=False)
    auto_delve_level = Column(Integer, nullable=True)  # null = max unlocked

    members = relationship('Adventurer', secondary=party_adventurer, back_populates='parties')
    expeditions = relationship('Expedition', foreign_keys='Expedition.party_id', back_populates='party')
    current_expedition = relationship('Expedition', foreign_keys=[current_expedition_id], post_update=True)
    keep = relationship('Keep', back_populates='parties')

class DungeonNode(Base):
    __tablename__ = 'dungeon_nodes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    difficulty = Column(Integer, default=1)
    description = Column(Text)

class Expedition(Base):
    __tablename__ = 'expeditions'

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'), nullable=False)
    start_day = Column(Integer, nullable=False)  # Game day when expedition started
    duration_days = Column(Integer, default=7)  # Default expedition duration in days
    return_day = Column(Integer, nullable=False)  # Game day when expedition will return
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    dungeon_level = Column(Integer, default=1)
    result = Column(String)  # 'in_progress', 'awaiting_choice', 'completed'
    pending_event = Column(JSON, nullable=True)  # Current interactive event awaiting player choice
    resolved_phases = Column(Integer, default=0)  # How many decision points resolved so far
    decision_day = Column(Integer, nullable=True)  # Game day when next decision fires
    simulation_data = Column(JSON, nullable=True)  # Stores sim results until expedition returns

    # Relationship to owning Party; specify foreign_keys to disambiguate multiple FKs between tables
    party = relationship(
        'Party',
        back_populates='expeditions',
        foreign_keys=[party_id]
    )
    node_results = relationship('ExpeditionNodeResult', back_populates='expedition')

class ExpeditionNodeResult(Base):
    __tablename__ = 'expedition_node_results'

    id = Column(Integer, primary_key=True)
    expedition_id = Column(Integer, ForeignKey('expeditions.id'), nullable=False)
    node_id = Column(Integer, ForeignKey('dungeon_nodes.id'), nullable=False)
    success = Column(Boolean)
    xp_earned = Column(Integer, default=0)
    loot = Column(Integer, default=0)
    log = Column(Text)

    expedition = relationship('Expedition', back_populates='node_results')
    node = relationship('DungeonNode')

# Simple log table for individual adventurer participation
class ExpeditionLog(Base):
    __tablename__ = 'expedition_logs'

    id = Column(Integer, primary_key=True)
    expedition_id = Column(Integer, ForeignKey('expeditions.id'), nullable=False)
    adventurer_id = Column(Integer, ForeignKey('adventurers.id'), nullable=False)
    xp_share = Column(Integer, default=0)
    hp_change = Column(Integer, default=0)
    status = Column(String)  # e.g., 'alive', 'wounded', 'dead'

    adventurer = relationship('Adventurer', back_populates='expedition_logs')


class MagicItem(Base):
    """A magic item owned by an adventurer."""
    __tablename__ = 'magic_items'

    id = Column(Integer, primary_key=True)
    adventurer_id = Column(Integer, ForeignKey('adventurers.id'), nullable=False)
    name = Column(String, nullable=False)
    item_type = Column(String, nullable=False)  # 'weapon' or 'armor'
    bonus = Column(Integer, default=1)  # +N bonus, equals dungeon level where found
    found_day = Column(Integer, nullable=True)
    found_expedition_id = Column(Integer, nullable=True)

    adventurer = relationship('Adventurer', back_populates='magic_items')
