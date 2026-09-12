from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class AdventurerClass(str, Enum):
    FIGHTER = 'Fighter'
    CLERIC = 'Cleric'
    MAGIC_USER = 'Magic-User'
    ELF = 'Elf'
    DWARF = 'Dwarf'
    HALFLING = 'Halfling'

class EncounterType(str, Enum):
    MONSTER = "Monster"
    TRAP = "Trap/Hazard"
    CLUE = "Clue or Empty Room"
    TREASURE = "Unguarded Treasure"

class CombatOutcome(str, Enum):
    VICTORY = "Victory"
    MONSTERS_FLED = "Monsters Fled"
    PARTY_FLED = "Party Fled"
    TPK = "TPK"

class LevelUpResult(BaseModel):
    old_level: int
    new_level: int
    hp_gained: int
    next_level_xp: int | None = None
    class_bonuses: dict[str, Any] = {}

class ClassAbilityOut(BaseModel):
    """A class ability the adventurer has unlocked, with uses per expedition."""
    name: str
    description: str
    uses: int | None = None  # None for passive abilities


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
    current_level_xp: int | None = None
    xp_progress: float | None = None
    # Combat stats (enriched by add_progression_data)
    thac0: int | None = None
    hit_dice: int | None = None
    to_hit_bonus: int | None = None
    to_hit: int | None = None  # d20-style: (20 - THAC0) + class bonus
    class_abilities: list[ClassAbilityOut] = []
    party_name: str | None = None

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
    adventurer_ids: list[int] = []

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

class AdventurerRef(BaseModel):
    """An adventurer named in an event message, so the UI can link to their sheet."""
    id: int
    name: str


class GameEvent(BaseModel):
    type: str  # 'recruitment', 'healing', 'expedition_complete', 'auto_start', 'upkeep', 'upkeep_deferred'
    message: str
    expedition_id: int | None = None
    first_time: bool = False
    event_subtype: str | None = None  # e.g. 'stairs', 'death', 'big_haul' for expedition_choice events
    data: dict | None = None  # structured payload, e.g. the upkeep-day ledger
    # Every adventurer named in `message`. The UI turns each name into a link
    # to that adventurer's sheet, so no name in a notification is a dead end.
    adventurers: list[AdventurerRef] = []

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
    actual_return_day: int | None = None  # set when the party came home early (retreat)
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


# ---- Feedback (buildplans/feedback-form-spec.md) ----

FeedbackCategory = Literal[
    "Something is broken",
    "I'm confused or stuck",
    "Something feels wrong",
    "I have an idea",
    "I like something",
]


class FeedbackCreate(BaseModel):
    category: FeedbackCategory
    doing: str = Field(max_length=500)
    feedback: str = Field(max_length=10000)
    severity: int | None = Field(default=None, ge=1, le=4)
    name: str | None = Field(default=None, max_length=100)
    page_url: str = Field(max_length=2048)

    @field_validator("doing", "feedback")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v


class FeedbackOut(BaseModel):
    id: int
