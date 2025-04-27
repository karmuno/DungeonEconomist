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
    
class EquipmentType(str, Enum):
    WEAPON = 'Weapon'
    ARMOR = 'Armor'
    SHIELD = 'Shield'
    MAGIC_ITEM = 'Magic Item'
    POTION = 'Potion'
    TOOL = 'Tool'
    MISCELLANEOUS = 'Miscellaneous'

class SupplyType(str, Enum):
    FOOD = 'Food'
    WATER = 'Water'
    LIGHT = 'Light'
    MEDICAL = 'Medical'
    TOOL = 'Tool'
    ADVENTURE = 'Adventure'
    MISCELLANEOUS = 'Miscellaneous'
    
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

class EquipmentBase(BaseModel):
    name: str
    equipment_type: EquipmentType
    description: Optional[str] = None
    cost: int = 0
    weight: float = 0
    properties: Optional[Dict[str, Any]] = None

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentOut(EquipmentBase):
    id: int
    
    class Config:
        from_attributes = True

class AdventurerEquipmentOut(BaseModel):
    equipment: EquipmentOut
    equipped: bool = False
    quantity: int = 1
    
    class Config:
        from_attributes = True

class SupplyBase(BaseModel):
    name: str
    supply_type: SupplyType
    description: Optional[str] = None
    cost: int = 0
    weight: float = 0
    uses_per_unit: int = 1

class SupplyCreate(SupplyBase):
    pass

class SupplyOut(SupplyBase):
    id: int
    
    class Config:
        from_attributes = True

class PartySupplyOut(BaseModel):
    supply: SupplyOut
    quantity: int = 1
    
    class Config:
        from_attributes = True

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
    is_available: bool
    on_expedition: bool = False
    expedition_status: Optional[str] = None
    healing_until_day: Optional[int] = None
    carry_capacity: int = 150
    equipment: Optional[List[AdventurerEquipmentOut]] = None
    next_level_xp: Optional[int] = None
    xp_progress: Optional[float] = None  # Percentage to next level (0-100)

    class Config:
        from_attributes = True
        
class AdventurerCreate(BaseModel):
    name: str
    adventurer_class: AdventurerClass
    level: int = 1
    hp_max: int = 10
    carry_capacity: Optional[int] = None
    
class PlayerBase(BaseModel):
    name: str

class PlayerCreate(PlayerBase):
    pass

class PlayerOut(PlayerBase):
    id: int
    treasury: int = 0
    total_score: int = 0
    
    class Config:
        from_attributes = True

class PartyBase(BaseModel):
    name: str
    
class PartyCreate(PartyBase):
    funds: int = 0
    player_id: Optional[int] = None
    
class PartyOut(PartyBase):
    id: int
    created_at: Optional[datetime] = None
    on_expedition: bool = False
    current_expedition_id: Optional[int] = None
    funds: int = 0
    player_id: Optional[int] = None
    members: List[AdventurerOut] = []
    supplies: Optional[List[PartySupplyOut]] = None
    
    class Config:
        from_attributes = True

class PartyStatusUpdate(BaseModel):
    on_expedition: bool
    current_expedition_id: Optional[int] = None

class PartyFundsUpdate(BaseModel):
    amount: int  # Positive to add funds, negative to remove funds
        
class PartyMemberOperation(BaseModel):
    party_id: int
    adventurer_id: int
    
class EquipmentOperation(BaseModel):
    adventurer_id: int
    equipment_id: int
    quantity: int = 1
    equip: Optional[bool] = None
    
class SupplyOperation(BaseModel):
    party_id: int
    supply_id: int
    quantity: int = 1
    
# --- Expedition schemas ---
class ExpeditionCreate(BaseModel):
    party_id: int
    dungeon_level: int = 1
    duration_days: int = 7
    supplies_to_bring: Optional[List[Dict[str, int]]] = None  # List of {supply_id: quantity} pairs
    
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

class GameTimeInfo(BaseModel):
    current_day: int
    day_started_at: datetime
    last_updated: datetime

class ExpeditionResult(BaseModel):
    expedition_id: int
    party_id: int
    dungeon_level: int
    turns: int
    start_day: int
    duration_days: int
    return_day: int
    start_time: datetime
    end_time: Optional[datetime] = None
    treasure_total: int
    special_items: List[str] = []
    xp_earned: float
    xp_per_party_member: float
    resources_used: Dict[str, Any]
    supplies_consumed: Optional[Dict[str, int]] = None
    equipment_lost: Optional[Dict[str, List[int]]] = None
    dead_members: List[str] = []
    party_status: PartyStatus
    log: List[TurnLog] = []
    party_members_ready_for_level_up: Optional[List[AdventurerLevelUpInfo]] = None
    
class TurnResult(BaseModel):
    turn: int
    events: List[Dict[str, Any]] = []
    party_status: PartyStatus
    expedition_ended: bool