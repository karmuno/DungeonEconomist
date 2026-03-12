from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.requests import Request
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models import (
    Adventurer, Party, Player, GameTime, Supply, Equipment,
    SupplyType, party_supply, party_adventurer
)
from app.schemas import (
    PartyOut, PartyCreate, PartyMemberOperation, PartyFundsUpdate,
    SupplyOut, SupplyCreate, SupplyOperation, PartySupplyOut
)
from app.routes.adventurers import add_progression_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/parties/", response_model=PartyOut)
def create_party(
    party_data: PartyCreate,
    db: Session = Depends(get_db)
):
    """Create a new party"""
    new_party = Party(
        name=party_data.name,
        created_at=datetime.now(),
        funds=party_data.funds,
        player_id=party_data.player_id
    )

    if party_data.player_id is not None:
        db_player = db.query(Player).filter(Player.id == party_data.player_id).first()
        if not db_player:
            raise HTTPException(status_code=404, detail="Player not found")

    db.add(new_party)
    db.commit()
    db.refresh(new_party)
    _ = new_party.members
    _ = new_party.supplies
    return new_party


@router.get("/parties/", response_model=list[PartyOut])
def list_parties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Party).offset(skip).limit(limit).all()


@router.get("/parties/create-form", response_class=HTMLResponse)
def party_create_form(request: Request, db: Session = Depends(get_db)):
    """Return the party creation form"""
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    return templates.TemplateResponse(
        "partials/party_form.html",
        {"request": request, "treasury_gold": treasury_gold}
    )


@router.get("/parties/{party_id}/edit-form", response_class=HTMLResponse)
def party_edit_form(request: Request, party_id: int, db: Session = Depends(get_db)):
    """Return the party editing form pre-populated with party data"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    players = db.query(Player).all()
    available_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    ).all()
    return templates.TemplateResponse(
        "partials/party_form_enhanced.html",
        {
            "request": request,
            "party": party,
            "players": players,
            "available_adventurers": available_adventurers
        }
    )


@router.get("/parties/{party_id}/add-member-form", response_class=HTMLResponse)
def party_add_member_form(request: Request, party_id: int, db: Session = Depends(get_db)):
    """Return the add-adventurer form for a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    available_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    ).all()
    return templates.TemplateResponse(
        "partials/add_party_member_enhanced.html",
        {"request": request, "party": party, "available_adventurers": available_adventurers}
    )


@router.put("/parties/{party_id}", response_model=PartyOut)
def update_party(
    party_id: int,
    party_data: PartyCreate,
    db: Session = Depends(get_db)
):
    """Update party details"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    party.name = party_data.name
    party.funds = party_data.funds
    party.player_id = party_data.player_id
    db.commit()
    db.refresh(party)
    return party


@router.get("/parties/{party_id}", response_model=PartyOut)
def get_party(party_id: int, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    return party


@router.get("/parties/{party_id}/status")
def get_party_expedition_status(party_id: int, db: Session = Depends(get_db)):
    """Get the expedition status of a party"""
    from app.models import Expedition
    party = db.query(Party).filter(Party.id == party_id).first()
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
            "expedition_status": member.expedition_status,
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
    db: Session = Depends(get_db)
):
    """Add an adventurer to a party."""
    party = db.query(Party).filter(Party.id == operation.party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Cannot add members to a party currently on expedition")
    adventurer = db.query(Adventurer).filter(
        Adventurer.id == operation.adventurer_id,
        Adventurer.is_available == True
    ).first()
    if adventurer is None:
        raise HTTPException(status_code=404, detail="Adventurer not found or not available")
    if adventurer in party.members:
        raise HTTPException(status_code=400, detail="Adventurer is already a member of this party")
    party.members.append(adventurer)
    db.commit()
    db.refresh(party)
    return party


@router.post("/parties/remove-member/", response_model=PartyOut)
def remove_adventurer_from_party(operation: PartyMemberOperation, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == operation.party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")

    if party.on_expedition:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove members from a party currently on expedition"
        )

    adventurer = db.query(Adventurer).filter(Adventurer.id == operation.adventurer_id).first()
    if adventurer is None:
        raise HTTPException(status_code=404, detail="Adventurer not found")

    if adventurer not in party.members:
        raise HTTPException(status_code=400, detail="Adventurer is not a member of this party")

    party.members.remove(adventurer)
    db.commit()
    db.refresh(party)
    return party


@router.put("/parties/{party_id}/funds", response_model=PartyOut)
def update_party_funds(
    party_id: int,
    funds_update: PartyFundsUpdate,
    db: Session = Depends(get_db)
):
    """Update a party's funds (add or remove gold)"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    if funds_update.amount < 0 and abs(funds_update.amount) > party.funds:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough funds. Attempting to remove {abs(funds_update.amount)}, Available: {party.funds}"
        )

    party.funds += funds_update.amount
    db.commit()
    db.refresh(party)
    return party


# --- Supply Endpoints ---

@router.post("/supplies/", response_model=SupplyOut)
def create_supply(supply: SupplyCreate, db: Session = Depends(get_db)):
    """Create a new supply item"""
    db_supply = Supply(
        name=supply.name,
        supply_type=supply.supply_type,
        description=supply.description,
        cost=supply.cost,
        weight=supply.weight,
        uses_per_unit=supply.uses_per_unit
    )
    db.add(db_supply)
    db.commit()
    db.refresh(db_supply)
    return db_supply


@router.get("/supplies/", response_model=List[SupplyOut])
def list_supplies(
    type_filter: Optional[SupplyType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all supply items, optionally filtered by type"""
    query = db.query(Supply)
    if type_filter:
        query = query.filter(Supply.supply_type == type_filter)
    return query.offset(skip).limit(limit).all()


@router.get("/supplies/{supply_id}", response_model=SupplyOut)
def get_supply(supply_id: int, db: Session = Depends(get_db)):
    """Get a specific supply item by ID"""
    supply = db.query(Supply).filter(Supply.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Supply not found")
    return supply


@router.post("/parties/{party_id}/supplies", response_model=PartyOut)
def add_supply_to_party(
    party_id: int,
    operation: SupplyOperation,
    db: Session = Depends(get_db)
):
    """Add supplies to a party's inventory"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Cannot modify supplies for party currently on expedition")

    supply = db.query(Supply).filter(Supply.id == operation.supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Supply not found")

    total_cost = supply.cost * operation.quantity
    if total_cost > party.funds:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough funds. Required: {total_cost}, Available: {party.funds}"
        )

    stmt = party_supply.select().where(
        party_supply.c.party_id == party_id,
        party_supply.c.supply_id == operation.supply_id
    )
    result = db.execute(stmt).first()

    if result:
        stmt = party_supply.update().where(
            party_supply.c.party_id == party_id,
            party_supply.c.supply_id == operation.supply_id
        ).values(quantity=result.quantity + operation.quantity)
        db.execute(stmt)
    else:
        stmt = party_supply.insert().values(
            party_id=party_id,
            supply_id=operation.supply_id,
            quantity=operation.quantity
        )
        db.execute(stmt)

    party.funds -= total_cost
    db.commit()
    db.refresh(party)
    return party


@router.delete("/parties/{party_id}/supplies/{supply_id}")
def remove_supply_from_party(
    party_id: int,
    supply_id: int,
    quantity: int = 1,
    db: Session = Depends(get_db)
):
    """Remove supplies from a party's inventory"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Cannot modify supplies for party currently on expedition")

    stmt = party_supply.select().where(
        party_supply.c.party_id == party_id,
        party_supply.c.supply_id == supply_id
    )
    result = db.execute(stmt).first()

    if not result:
        raise HTTPException(status_code=404, detail="Supply not found in party's inventory")

    if result.quantity <= quantity:
        stmt = party_supply.delete().where(
            party_supply.c.party_id == party_id,
            party_supply.c.supply_id == supply_id
        )
    else:
        stmt = party_supply.update().where(
            party_supply.c.party_id == party_id,
            party_supply.c.supply_id == supply_id
        ).values(quantity=result.quantity - quantity)

    db.execute(stmt)
    db.commit()

    return {"message": "Supply removed successfully"}


# --- Frontend Routes ---

@router.get("/parties", response_class=HTMLResponse)
def parties_page(request: Request, db: Session = Depends(get_db)):
    """Render the parties page"""
    parties = db.query(Party).all()

    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury

    game_time = db.query(GameTime).first()

    return templates.TemplateResponse(
        "parties_enhanced.html",
        {
            "request": request,
            "parties": parties,
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )


@router.get("/ui/get-party-list", response_class=HTMLResponse)
def get_party_list_html(
    request: Request,
    filter_type: Optional[str] = "all",
    sort_by: Optional[str] = "name",
    db: Session = Depends(get_db)
):
    """Get HTML partial for the party list, with optional filtering and sorting."""
    query = db.query(Party)

    if filter_type == "available":
        query = query.filter(Party.on_expedition == False)
    elif filter_type == "expedition":
        query = query.filter(Party.on_expedition == True)

    if sort_by == "members":
        member_count = db.query(
            party_adventurer.c.party_id,
            func.count(party_adventurer.c.adventurer_id).label('member_count')
        ).group_by(party_adventurer.c.party_id).subquery()

        query = query.outerjoin(
            member_count,
            Party.id == member_count.c.party_id
        ).order_by(member_count.c.member_count.desc(), Party.name)
    elif sort_by == "funds":
        query = query.order_by(Party.funds.desc(), Party.name)
    else:
        query = query.order_by(Party.name)

    parties = query.all()

    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury

    game_time = db.query(GameTime).first()

    return templates.TemplateResponse(
        "partials/party_list_container.html",
        {
            "request": request,
            "parties": parties,
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )


@router.get("/parties/sort", response_class=HTMLResponse)
def sort_parties(
    request: Request,
    sort_by: Optional[str] = "name",
    filter_type: Optional[str] = "all",
    db: Session = Depends(get_db)
):
    """Sort parties by different criteria"""
    return get_party_list_html(request, filter_type, sort_by, db)


@router.get("/parties/{party_id}/filter-adventurers", response_class=HTMLResponse)
def filter_party_adventurers(
    request: Request,
    party_id: int,
    class_filter: Optional[str] = "",
    level_filter: Optional[str] = "",
    db: Session = Depends(get_db)
):
    """Filter available adventurers for adding to a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    query = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    )

    if class_filter and class_filter != "":
        query = query.filter(Adventurer.adventurer_class == class_filter)

    if level_filter and level_filter != "":
        min_level = int(level_filter)
        query = query.filter(Adventurer.level >= min_level)

    available_adventurers = query.order_by(Adventurer.level.desc(), Adventurer.name).all()
    available_adventurers = [add_progression_data(adv) for adv in available_adventurers]

    game_time = db.query(GameTime).first()

    return templates.TemplateResponse(
        "partials/available_adventurers_list.html",
        {
            "request": request,
            "party": party,
            "available_adventurers": available_adventurers,
            "game_time": game_time
        }
    )


@router.get("/parties/{party_id}/supplies", response_class=HTMLResponse)
def party_supplies_page(
    request: Request,
    party_id: int,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Show and manage party supplies"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    supply_types = list(SupplyType)
    query = db.query(Supply)
    if type:
        query = query.filter(Supply.supply_type == type)
    available_supplies = query.order_by(Supply.supply_type, Supply.cost, Supply.name).all()

    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury

    return templates.TemplateResponse(
        "partials/party_supplies.html",
        {
            "request": request,
            "party": party,
            "supply_types": supply_types,
            "available_supplies": available_supplies,
            "active_filter": type,
            "treasury_gold": treasury_gold
        }
    )


@router.get("/parties/{party_id}/add-funds-form", response_class=HTMLResponse)
def add_party_funds_form(
    request: Request,
    party_id: int,
    db: Session = Depends(get_db)
):
    """Show form to add funds to a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    return templates.TemplateResponse(
        "partials/party_funds_form.html",
        {"request": request, "party": party, "action": "add"}
    )


@router.get("/parties/{party_id}/remove-funds-form", response_class=HTMLResponse)
def remove_party_funds_form(
    request: Request,
    party_id: int,
    db: Session = Depends(get_db)
):
    """Show form to remove funds from a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    return templates.TemplateResponse(
        "partials/party_funds_form.html",
        {"request": request, "party": party, "action": "remove"}
    )
