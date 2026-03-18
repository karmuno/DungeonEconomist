from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_keep
from app.database import get_db
from app.models import Adventurer, Keep, Party
from app.schemas import PartyCreate, PartyMemberOperation, PartyOut

router = APIRouter()


@router.post("/parties/", response_model=PartyOut)
def create_party(
    party_data: PartyCreate,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Create a new party"""
    new_party = Party(
        name=party_data.name,
        created_at=datetime.now(),
        keep_id=keep.id,
    )
    db.add(new_party)
    db.commit()
    db.refresh(new_party)
    _ = new_party.members
    return new_party


@router.get("/parties/", response_model=list[PartyOut])
def list_parties(
    skip: int = 0,
    limit: int = 100,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    return db.query(Party).filter(Party.keep_id == keep.id).offset(skip).limit(limit).all()


@router.put("/parties/{party_id}", response_model=PartyOut)
def update_party(
    party_id: int,
    party_data: PartyCreate,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Update party details"""
    party = db.query(Party).filter(Party.id == party_id, Party.keep_id == keep.id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    party.name = party_data.name
    db.commit()
    db.refresh(party)
    return party


@router.get("/parties/{party_id}", response_model=PartyOut)
def get_party(
    party_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    party = db.query(Party).filter(Party.id == party_id, Party.keep_id == keep.id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    return party


@router.get("/parties/{party_id}/status")
def get_party_expedition_status(
    party_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Get the expedition status of a party"""
    from app.models import Expedition
    party = db.query(Party).filter(Party.id == party_id, Party.keep_id == keep.id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")

    current_expedition = None
    if party.on_expedition and party.current_expedition_id:
        current_expedition = db.query(Expedition).filter(
            Expedition.id == party.current_expedition_id
        ).first()

    members_status = []
    for member in party.members:
        members_status.append({
            "id": member.id,
            "name": member.name,
            "class": member.adventurer_class.value,
            "hp_current": member.hp_current,
            "hp_max": member.hp_max,
            "hp_percentage": (member.hp_current / member.hp_max) * 100 if member.hp_max > 0 else 0,
            "on_expedition": member.on_expedition,
            "is_available": member.is_available
        })

    return {
        "party_id": party.id,
        "party_name": party.name,
        "on_expedition": party.on_expedition,
        "current_expedition_id": party.current_expedition_id,
        "expedition_status": current_expedition.result if current_expedition else None,
        "members_status": members_status,
        "members_total": len(party.members),
        "members_available": sum(1 for m in party.members if m.is_available),
        "members_on_expedition": sum(1 for m in party.members if m.on_expedition),
        "party_health": sum(m.hp_current for m in party.members),
        "party_max_health": sum(m.hp_max for m in party.members),
        "party_health_percentage": (sum(m.hp_current for m in party.members) /
                                   sum(m.hp_max for m in party.members)) * 100
                                   if party.members and sum(m.hp_max for m in party.members) > 0 else 0
    }


@router.post("/parties/add-member/", response_model=PartyOut)
def add_adventurer_to_party(
    operation: PartyMemberOperation,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Add an adventurer to a party."""
    party = db.query(Party).filter(Party.id == operation.party_id, Party.keep_id == keep.id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Cannot add members to a party currently on expedition")
    adventurer = db.query(Adventurer).filter(
        Adventurer.id == operation.adventurer_id,
        Adventurer.keep_id == keep.id,
        Adventurer.is_available == True
    ).first()
    if adventurer is None:
        raise HTTPException(status_code=404, detail="Adventurer not found or not available")
    if adventurer in party.members:
        raise HTTPException(status_code=400, detail="Adventurer is already a member of this party")
    if len(party.members) >= 6:
        raise HTTPException(status_code=400, detail="Party is full (max 6 members)")
    party.members.append(adventurer)
    db.commit()
    db.refresh(party)
    return party


@router.post("/parties/remove-member/", response_model=PartyOut)
def remove_adventurer_from_party(
    operation: PartyMemberOperation,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    party = db.query(Party).filter(Party.id == operation.party_id, Party.keep_id == keep.id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")

    if party.on_expedition:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove members from a party currently on expedition"
        )

    adventurer = db.query(Adventurer).filter(
        Adventurer.id == operation.adventurer_id,
        Adventurer.keep_id == keep.id,
    ).first()
    if adventurer is None:
        raise HTTPException(status_code=404, detail="Adventurer not found")

    if adventurer not in party.members:
        raise HTTPException(status_code=400, detail="Adventurer is not a member of this party")

    party.members.remove(adventurer)
    db.commit()
    db.refresh(party)
    return party


class AutoDelveUpdate(BaseModel):
    auto_delve_healed: bool = False
    auto_delve_full: bool = False
    auto_decide_events: bool = False
    auto_delve_level: int | None = None  # null = max unlocked


@router.put("/parties/{party_id}/auto-delve")
def update_auto_delve(
    party_id: int,
    data: AutoDelveUpdate,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Update auto-delve and auto-decide settings for a party."""
    party = db.query(Party).filter(Party.id == party_id, Party.keep_id == keep.id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    party.auto_delve_healed = data.auto_delve_healed
    party.auto_delve_full = data.auto_delve_full
    party.auto_decide_events = data.auto_decide_events
    party.auto_delve_level = data.auto_delve_level
    db.commit()
    return {"ok": True}


@router.delete("/parties/{party_id}")
def delete_party(
    party_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Delete a party and its associated expeditions. Cannot delete parties on expedition."""
    party = db.query(Party).filter(Party.id == party_id, Party.keep_id == keep.id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Cannot delete a party currently on expedition")
    # Clear FK references before deleting
    from app.models import Expedition, ExpeditionLog, ExpeditionNodeResult
    party.current_expedition_id = None
    party.members.clear()
    db.flush()
    # Delete associated expedition data
    expeditions = db.query(Expedition).filter(Expedition.party_id == party_id).all()
    for exp in expeditions:
        db.query(ExpeditionNodeResult).filter(ExpeditionNodeResult.expedition_id == exp.id).delete()
        db.query(ExpeditionLog).filter(ExpeditionLog.expedition_id == exp.id).delete()
    db.flush()
    for exp in expeditions:
        db.delete(exp)
    db.flush()
    db.delete(party)
    db.commit()
    return {"ok": True}
