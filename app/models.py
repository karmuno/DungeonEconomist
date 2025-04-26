from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

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
    name = Column(String, nullable=False)
    adventurer_class = Column(Enum(AdventurerClass), nullable=False)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    hp_current = Column(Integer, default=10)
    hp_max = Column(Integer, default=10)
    gold = Column(Integer, default=0)
    is_available = Column(Boolean, default=True)

    parties = relationship('Party', secondary=party_adventurer, back_populates='members')
    expedition_logs = relationship('ExpeditionLog', back_populates='adventurer')

class Party(Base):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    name = Column(String, default='New Party')
    created_at = Column(DateTime)

    members = relationship('Adventurer', secondary=party_adventurer, back_populates='parties')
    expeditions = relationship('Expedition', back_populates='party')

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
