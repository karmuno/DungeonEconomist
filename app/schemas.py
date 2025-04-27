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

class AdventurerOut(BaseModel):
    id: int
    name: str
    adventurer_class: AdventurerClass
    level: int
    xp: int
    hp_current: int
    hp_max: int
    gold: int
    is_available: bool

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
    members: List[AdventurerOut] = []
    
    class Config:
        from_attributes = True
        
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
    
class ExpeditionResult(BaseModel):
    expedition_id: int
    party_id: int
    dungeon_level: int
    turns: int
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
    
class TurnResult(BaseModel):
    turn: int
    events: List[Dict[str, Any]] = []
    party_status: PartyStatus
    expedition_ended: bool