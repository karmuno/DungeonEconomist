from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, field_validator


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
    next_level_xp: int | None = None
    class_bonuses: dict[str, Any] = {}

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
    is_assigned: bool = False
    is_bankrupt: bool = False
    is_dead: bool = False
    death_day: int | None = None
    death_party_name: str | None = None
    bankruptcy_day: int | None = None
    magic_items: list[dict[str, Any]] = []
    next_level_xp: int | None = None
    xp_progress: float | None = None

    @field_validator('magic_items', mode='before')
    @classmethod
    def serialize_magic_items(cls, v):
        if not v:
            return []
        result = []
        for item in v:
            if isinstance(item, dict):
                result.append(item)
            else:
                result.append({
                    "id": item.id,
                    "name": item.name,
                    "item_type": item.item_type,
                    "bonus": item.bonus or 0,
                })
        return result

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
    created_at: datetime | None = None
    on_expedition: bool = False
    current_expedition_id: int | None = None
    keep_id: int | None = None
    auto_delve_healed: bool = False
    auto_delve_full: bool = False
    auto_decide_events: bool = False
    auto_delve_level: int | None = None
    members: list[AdventurerOut] = []

    class Config:
        from_attributes = True

class PartyStatusUpdate(BaseModel):
    on_expedition: bool
    current_expedition_id: int | None = None

class PartyMemberOperation(BaseModel):
    party_id: int
    adventurer_id: int

# --- Expedition schemas ---
class ExpeditionCreate(BaseModel):
    party_id: int
    dungeon_level: int = 1

class TreasureItem(BaseModel):
    gold: int
    special_item: str | None = None
    xp_value: int

class CombatResult(BaseModel):
    outcome: CombatOutcome
    monster_type: str
    hp_lost: int
    xp_earned: int

class EncounterEvent(BaseModel):
    type: EncounterType
    combat: CombatResult | None = None
    treasure: TreasureItem | None = None
    trap_damage: int | None = None

class TurnLog(BaseModel):
    turn: int
    events: list[EncounterEvent] = []

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
    expedition_id: int | None = None
    first_time: bool = False

class GameTimeInfo(BaseModel):
    current_day: int
    day_started_at: datetime
    last_updated: datetime

class AdvanceDayResult(BaseModel):
    current_day: int
    day_started_at: datetime
    last_updated: datetime
    events: list[GameEvent] = []

class ExpeditionResult(BaseModel):
    expedition_id: int
    party_id: int
    dungeon_level: int
    turns: int
    start_day: int | None = None
    duration_days: int | None = None
    return_day: int | None = None
    start_time: datetime
    end_time: datetime | None = None
    treasure_total: int
    treasure_silver: int = 0
    treasure_copper: int = 0
    special_items: list[str] = []
    xp_earned: float
    xp_per_party_member: float
    resources_used: dict[str, Any]
    dead_members: list[str] = []
    party_status: PartyStatus
    log: list[TurnLog] = []
    party_members_ready_for_level_up: list[AdventurerLevelUpInfo] | None = None

class TurnResult(BaseModel):
    turn: int
    events: list[dict[str, Any]] = []
    party_status: PartyStatus
    expedition_ended: bool
