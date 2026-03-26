import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.auth import get_current_account
from app.database import get_db
from app.dungeons import DUNGEON_LEVELS, generate_dungeon_name, generate_level_names
from app.models import Account, Adventurer, AdventurerClass, Keep
from app.names import generate_adventurer_name

router = APIRouter(prefix="/keeps", tags=["keeps"])


class KeepCreate(BaseModel):
    name: str


class KeepOut(BaseModel):
    id: int
    name: str
    treasury_gold: int
    treasury_silver: int
    treasury_copper: int
    total_score: int
    current_day: int
    day_started_at: datetime
    last_updated: datetime
    created_at: datetime
    dungeon_name: str | None = None
    max_dungeon_level: int = 1
    building_types: list[str] = []

    @field_validator('max_dungeon_level', mode='before')
    @classmethod
    def default_dungeon_level(cls, v):
        return v if v is not None else 1

    class Config:
        from_attributes = True


def roll_hp(adventurer_class: AdventurerClass) -> int:
    base = random.randint(1, 6)
    if adventurer_class in (AdventurerClass.FIGHTER, AdventurerClass.DWARF):
        return base + 2
    return base


def seed_starting_adventurers(keep: Keep, db: Session) -> list[Adventurer]:
    """Create 6 starting adventurers (one per class) for a new keep."""
    adventurers = []
    for adv_class in AdventurerClass:
        hp = roll_hp(adv_class)
        adv = Adventurer(
            keep_id=keep.id,
            name=generate_adventurer_name(adv_class),
            adventurer_class=adv_class,
            level=1,
            xp=0,
            hp_max=hp,
            hp_current=hp,
            gold=0,
            is_available=True,
        )
        db.add(adv)
        adventurers.append(adv)
    return adventurers


@router.get("/", response_model=list[KeepOut])
def list_keeps(account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    return db.query(Keep).filter(Keep.account_id == account.id).all()


@router.post("/", response_model=KeepOut)
def create_keep(data: KeepCreate, account: Account = Depends(get_current_account), db: Session = Depends(get_db)):
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="Keep name is required")

    now = datetime.now()
    keep = Keep(
        account_id=account.id,
        name=data.name.strip(),
        treasury_gold=0,
        treasury_silver=0,
        treasury_copper=0,
        total_score=0,
        current_day=1,
        day_started_at=now,
        last_updated=now,
        created_at=now,
        dungeon_name=generate_dungeon_name(),
        dungeon_level_names=generate_level_names(len(DUNGEON_LEVELS)),
        max_dungeon_level=1,
    )
    db.add(keep)
    db.commit()
    db.refresh(keep)

    # Seed 6 starting adventurers
    seed_starting_adventurers(keep, db)
    db.commit()

    return keep


@router.delete("/{keep_id}")
def delete_keep(
    keep_id: int,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    from app.models import Expedition, ExpeditionLog, ExpeditionNodeResult, Party, party_adventurer

    keep = db.query(Keep).filter(Keep.id == keep_id, Keep.account_id == account.id).first()
    if not keep:
        raise HTTPException(status_code=404, detail="Keep not found")

    # Delete in dependency order
    parties = db.query(Party).filter(Party.keep_id == keep.id).all()
    party_ids = [p.id for p in parties]

    if party_ids:
        # Clear party-adventurer associations
        db.execute(party_adventurer.delete().where(party_adventurer.c.party_id.in_(party_ids)))

        # Delete expedition data
        expeditions = db.query(Expedition).filter(Expedition.party_id.in_(party_ids)).all()
        exp_ids = [e.id for e in expeditions]
        if exp_ids:
            db.query(ExpeditionNodeResult).filter(ExpeditionNodeResult.expedition_id.in_(exp_ids)).delete(synchronize_session=False)
            db.query(ExpeditionLog).filter(ExpeditionLog.expedition_id.in_(exp_ids)).delete(synchronize_session=False)
            db.query(Expedition).filter(Expedition.id.in_(exp_ids)).delete(synchronize_session=False)

        # Clear current_expedition_id FKs before deleting parties
        for p in parties:
            p.current_expedition_id = None
        db.flush()
        db.query(Party).filter(Party.keep_id == keep.id).delete(synchronize_session=False)

    # Delete adventurers
    db.query(Adventurer).filter(Adventurer.keep_id == keep.id).delete(synchronize_session=False)

    db.delete(keep)
    db.commit()
    return {"ok": True}
