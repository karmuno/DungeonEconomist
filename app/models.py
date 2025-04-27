from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Enum, Boolean, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    treasury = Column(Integer, default=0)  # Treasury for collecting gold (30% of loot)
    total_score = Column(Integer, default=0)  # Total gold collected over time (for scoring)
    
    parties = relationship('Party', back_populates='player')

# Association table between Party and Adventurer
party_adventurer = Table(
    'party_adventurer', Base.metadata,
    Column('party_id', Integer, ForeignKey('parties.id'), primary_key=True),
    Column('adventurer_id', Integer, ForeignKey('adventurers.id'), primary_key=True)
)

# Association table between Adventurer and Equipment
adventurer_equipment = Table(
    'adventurer_equipment', Base.metadata,
    Column('adventurer_id', Integer, ForeignKey('adventurers.id'), primary_key=True),
    Column('equipment_id', Integer, ForeignKey('equipment.id'), primary_key=True),
    Column('equipped', Boolean, default=False),
    Column('quantity', Integer, default=1)
)

# Association table between Party and Supply
party_supply = Table(
    'party_supply', Base.metadata,
    Column('party_id', Integer, ForeignKey('parties.id'), primary_key=True),
    Column('supply_id', Integer, ForeignKey('supplies.id'), primary_key=True),
    Column('quantity', Integer, default=1)
)

class AdventurerClass(enum.Enum):
    FIGHTER = 'Fighter'
    CLERIC = 'Cleric'
    MAGIC_USER = 'Magic-User'
    ELF = 'Elf'
    DWARF = 'Dwarf'
    HOBBIT = 'Hobbit'

class EquipmentType(enum.Enum):
    WEAPON = 'Weapon'
    ARMOR = 'Armor'
    SHIELD = 'Shield'
    MAGIC_ITEM = 'Magic Item'
    POTION = 'Potion'
    TOOL = 'Tool'
    MISCELLANEOUS = 'Miscellaneous'

class SupplyType(enum.Enum):
    FOOD = 'Food'
    WATER = 'Water'
    LIGHT = 'Light'
    MEDICAL = 'Medical'
    TOOL = 'Tool'
    ADVENTURE = 'Adventure'
    MISCELLANEOUS = 'Miscellaneous'

class Equipment(Base):
    __tablename__ = 'equipment'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    equipment_type = Column(Enum(EquipmentType), nullable=False)
    description = Column(Text)
    cost = Column(Integer, default=0)
    weight = Column(Float, default=0)
    properties = Column(JSON, nullable=True)  # JSON for flexible properties
    
    # Relationships
    owners = relationship('Adventurer', secondary=adventurer_equipment, backref='equipment')

class Supply(Base):
    __tablename__ = 'supplies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    supply_type = Column(Enum(SupplyType), nullable=False)
    description = Column(Text)
    cost = Column(Integer, default=0)
    weight = Column(Float, default=0)
    uses_per_unit = Column(Integer, default=1)
    
    # Relationships
    parties = relationship('Party', secondary=party_supply, backref='supplies')

class Adventurer(Base):
    __tablename__ = 'adventurers'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    adventurer_class = Column(Enum(AdventurerClass), nullable=False)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    hp_current = Column(Integer, default=10)
    hp_max = Column(Integer, default=10)
    gold = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)
    on_expedition = Column(Boolean, default=False)
    expedition_status = Column(String, nullable=True)  # e.g., 'active', 'injured', 'resting'
    carry_capacity = Column(Integer, default=150)  # in pounds/units

    parties = relationship('Party', secondary=party_adventurer, back_populates='members')
    expedition_logs = relationship('ExpeditionLog', back_populates='adventurer')
    # Equipment is accessed through backref

class Party(Base):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    name = Column(String, default='New Party')
    created_at = Column(DateTime)
    on_expedition = Column(Boolean, default=False)
    current_expedition_id = Column(Integer, ForeignKey('expeditions.id', ondelete='SET NULL'), nullable=True)
    funds = Column(Integer, default=0)  # Party treasury in gold pieces (70% of loot)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    
    members = relationship('Adventurer', secondary=party_adventurer, back_populates='parties')
    expeditions = relationship('Expedition', foreign_keys='Expedition.party_id', back_populates='party')
    current_expedition = relationship('Expedition', foreign_keys='Party.current_expedition_id', post_update=True)
    player = relationship('Player', back_populates='parties')
    # Supplies are accessed through backref

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
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    result = Column(String)  # e.g., 'success', 'failure'
    supplies_consumed = Column(JSON, nullable=True)  # Tracks supplies consumed during expedition
    equipment_lost = Column(JSON, nullable=True)  # Tracks equipment lost/broken during expedition

    party = relationship('Party', back_populates='expeditions')
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
