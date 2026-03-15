from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime

class AdventurerClass(str, Enum):
    FIGHTER = 'Fighter'
    CLERIC = 'Cleric'
    MAGIC_USER = 'Magic-User'
    ELF = 'Elf'
    DWARF = 'Dwarf'
    HOBBIT = 'Hobbit'

class EncounterType(str, Enum):
    MONSTER = "Monster"
    TRAP = "Trap/Hazard"
    CLUE = "Clue or Empty Room"
    TREASURE = "Unguarded Treasure"

class CombatOutcome(str, Enum):
    CLEAR_VICTORY = "Clear Victory"
    VICTORY = "Victory"
    TOUGH_FIGHT = "Tough Fight"
    RETREAT = "Retreat"
    DISASTER = "Disaster"

class LevelUpResult(BaseModel):
    old_level: int
    new_level: int
    hp_gained: int
    next_level_xp: Optional[int] = None
    class_bonuses: Dict[str, Any] = {}

class AdventurerOut(BaseModel):
    id: int
    name: str
    adventurer_class: AdventurerClass
    level: int
    xp: int
    hp_current: int
    hp_max: int
    gold: int
    silver: int = 0
    copper: int = 0
    is_available: bool
    on_expedition: bool = False
    is_bankrupt: bool = False
    is_dead: bool = False
    death_day: Optional[int] = None
    death_party_name: Optional[str] = None
    bankruptcy_day: Optional[int] = None
    next_level_xp: Optional[int] = None
    xp_progress: Optional[float] = None

    class Config:
        from_attributes = True

class AdventurerCreate(BaseModel):
    name: str
    adventurer_class: AdventurerClass
    level: int = 1
    hp_max: int = 10

class PartyBase(BaseModel):
    name: str

class PartyCreate(PartyBase):
    pass

class PartyOut(PartyBase):
    id: int
    created_at: Optional[datetime] = None
    on_expedition: bool = False
    current_expedition_id: Optional[int] = None
    keep_id: Optional[int] = None
    members: List[AdventurerOut] = []

    class Config:
        from_attributes = True

class PartyStatusUpdate(BaseModel):
    on_expedition: bool
    current_expedition_id: Optional[int] = None

class PartyMemberOperation(BaseModel):
    party_id: int
    adventurer_id: int

# --- Expedition schemas ---
class ExpeditionCreate(BaseModel):
    party_id: int
    dungeon_level: int = 1

class TreasureItem(BaseModel):
    gold: int
    special_item: Optional[str] = None
    xp_value: int

class CombatResult(BaseModel):
    outcome: CombatOutcome
    monster_type: str
    hp_lost: int
    xp_earned: int

class EncounterEvent(BaseModel):
    type: EncounterType
    combat: Optional[CombatResult] = None
    treasure: Optional[TreasureItem] = None
    trap_damage: Optional[int] = None

class TurnLog(BaseModel):
    turn: int
    events: List[EncounterEvent] = []

class PartyStatus(BaseModel):
    members_total: int
    members_alive: int
    members_dead: int
    hp_current: int
    hp_max: int
    hp_percentage: float

class AdventurerLevelUpInfo(BaseModel):
    id: int
    name: str
    current_level: int
    next_level: int

class GameEvent(BaseModel):
    type: str  # 'recruitment', 'healing', 'expedition_complete', 'auto_start', 'upkeep'
    message: str
    expedition_id: Optional[int] = None

class GameTimeInfo(BaseModel):
    current_day: int
    day_started_at: datetime
    last_updated: datetime

class AdvanceDayResult(BaseModel):
    current_day: int
    day_started_at: datetime
    last_updated: datetime
    events: List[GameEvent] = []

class ExpeditionResult(BaseModel):
    expedition_id: int
    party_id: int
    dungeon_level: int
    turns: int
    start_day: Optional[int] = None
    duration_days: Optional[int] = None
    return_day: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    treasure_total: int
    special_items: List[str] = []
    xp_earned: float
    xp_per_party_member: float
    resources_used: Dict[str, Any]
    dead_members: List[str] = []
    party_status: PartyStatus
    log: List[TurnLog] = []
    party_members_ready_for_level_up: Optional[List[AdventurerLevelUpInfo]] = None

class TurnResult(BaseModel):
    turn: int
    events: List[Dict[str, Any]] = []
    party_status: PartyStatus
    expedition_ended: bool
