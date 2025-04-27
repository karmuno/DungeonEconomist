from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime

class AdventurerClass(str, Enum):
    FIGHTER = 'Fighter'
    CLERIC = 'Cleric'
    MAGIC_USER = 'Magic-User'
    ELF = 'Elf'
    DWARF = 'Dwarf'
    HOBBIT = 'Hobbit'

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
        orm_mode = True
        
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
        orm_mode = True
        
class PartyMemberOperation(BaseModel):
    party_id: int
    adventurer_id: int