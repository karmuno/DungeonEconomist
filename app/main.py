from fastapi import FastAPI, HTTPException, Depends, Body, Form, Query
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json
import math # Added for math.floor
from typing import List, Optional

from app.models import (
    Base, Adventurer, Party, DungeonNode, Expedition, 
    ExpeditionNodeResult, ExpeditionLog, Equipment, Supply,
    EquipmentType, SupplyType, adventurer_equipment, party_supply,
    Player, GameTime, party_adventurer
)
from app.schemas import (
    AdventurerOut, AdventurerCreate, PartyCreate, 
    PartyOut, PartyMemberOperation, ExpeditionCreate,
    ExpeditionResult, TurnResult, EquipmentOut, EquipmentCreate,
    SupplyOut, SupplyCreate, EquipmentOperation, SupplyOperation,
    PartyFundsUpdate, AdventurerEquipmentOut, PartySupplyOut,
    LevelUpResult, PlayerCreate, PlayerOut, PlayerBase, GameTimeInfo
)
from app.simulator import DungeonSimulator, calculate_loot_split
from app.progression import (
    calculate_xp_for_next_level, check_for_level_up,
    calculate_hp_gain, get_class_level_bonuses
)

DATABASE_URL = "sqlite:///./data/db.sqlite"

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title="Venturekeep",
    description="D&D Party Management Simulation",
    version="0.1.0"
)

# CORS (for local dev/frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to add progression data to adventurer
def add_progression_data(adventurer):
    next_level_xp = calculate_xp_for_next_level(adventurer.level)
    
    # Calculate progress to next level (as percentage)
    if next_level_xp:
        current_level_xp = calculate_xp_for_next_level(adventurer.level - 1) or 0
        xp_for_current_level = adventurer.xp - current_level_xp
        xp_needed_for_next = next_level_xp - current_level_xp
        progress = (xp_for_current_level / xp_needed_for_next) * 100 if xp_needed_for_next > 0 else 100
    else:
        # Max level
        progress = 100
    
    # Add computed fields (these won't be stored in DB but will be in response)
    adventurer.next_level_xp = next_level_xp
    adventurer.xp_progress = min(100, max(0, progress))
    return adventurer

# --- Adventurer Endpoints ---
@app.post("/adventurers/", response_model=AdventurerOut)
def create_adventurer(adventurer: AdventurerCreate, db: Session = Depends(get_db)):
    # Create new adventurer with initial stats
    adv = Adventurer(
        name=adventurer.name,
        adventurer_class=adventurer.adventurer_class,
        level=adventurer.level,
        hp_max=adventurer.hp_max,
        hp_current=adventurer.hp_max,  # Start with full HP
        xp=0,
        gold=0,
        is_available=True,
        carry_capacity=adventurer.carry_capacity or 150  # Default or provided value
    )
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return add_progression_data(adv)

@app.get("/adventurers/", response_model=list[AdventurerOut])
def list_adventurers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    adventurers = db.query(Adventurer).offset(skip).limit(limit).all()
    return [add_progression_data(adv) for adv in adventurers]

@app.get("/adventurers/{adventurer_id}", response_model=AdventurerOut)
def get_adventurer(adventurer_id: int, db: Session = Depends(get_db)):
    """Get a specific adventurer by ID"""
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    return add_progression_data(adventurer)

@app.post("/adventurers/{adventurer_id}/level-up", response_model=LevelUpResult)
def level_up_adventurer(adventurer_id: int, db: Session = Depends(get_db)):
    """Level up an adventurer if they have enough XP"""
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")

    # Check if adventurer is on expedition
    if adventurer.on_expedition:
        raise HTTPException(
            status_code=400,
            detail="Cannot level up an adventurer while they are on an expedition"
        )
    
    # Check if the adventurer has enough XP to level up
    if not check_for_level_up(adventurer.level, adventurer.xp):
        raise HTTPException(
            status_code=400,
            detail="Not enough XP to level up"
        )
    
    # Store the old level for the response
    old_level = adventurer.level
    
    # Perform the level up
    adventurer.level += 1
    
    # Calculate and add HP based on class
    hp_gain = calculate_hp_gain(adventurer.adventurer_class, old_level)
    adventurer.hp_max += hp_gain
    adventurer.hp_current += hp_gain  # Also heal for the amount gained
    
    # Apply class-specific bonuses
    class_bonuses = get_class_level_bonuses(adventurer.adventurer_class, adventurer.level)
    
    # Update carry capacity if applicable
    if "carry_capacity_bonus" in class_bonuses:
        adventurer.carry_capacity += int(class_bonuses["carry_capacity_bonus"])
    
    # Save changes
    db.commit()
    db.refresh(adventurer)
    
    # Calculate XP needed for next level (if any)
    next_level_xp = calculate_xp_for_next_level(adventurer.level)
    
    # Return the level up result
    return {
        "old_level": old_level,
        "new_level": adventurer.level,
        "hp_gained": hp_gain,
        "next_level_xp": next_level_xp,
        "class_bonuses": class_bonuses
    }

# --- Player Endpoints ---
@app.post("/players/", response_model=PlayerOut)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player"""
    db_player = Player(
        name=player.name,
        treasury=0,
        total_score=0
    )
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

@app.get("/players/", response_model=List[PlayerOut])
def list_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all players"""
    players = db.query(Player).offset(skip).limit(limit).all()
    return players

@app.get("/players/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player by ID"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.put("/players/{player_id}", response_model=PlayerOut)
def update_player(player_id: int, player_data: PlayerBase, db: Session = Depends(get_db)):
    """Update a player's information"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player.name = player_data.name
    db.commit()
    db.refresh(player)
    return player

@app.get("/players/{player_id}/parties", response_model=List[PartyOut])
def get_player_parties(player_id: int, db: Session = Depends(get_db)):
    """Get all parties belonging to a player"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player.parties

# --- Game/Utility Endpoints ---
@app.put("/upkeep")
def run_upkeep(db: Session = Depends(get_db)):
    """
    Run daily upkeep tasks.
    If current_day is a multiple of 30, charge upkeep costs to adventurers.
    Upkeep cost is 1% of XP (floored). If adventurer cannot pay, they go bankrupt.
    """
    game_time = db.query(GameTime).first()
    if not game_time:
        # Initialize GameTime if it doesn't exist
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)

    if game_time.current_day % 30 == 0:
        adventurers = db.query(Adventurer).all()
        adventurers_processed = 0
        bankrupt_adventurers = 0
        total_gold_deducted_from_adventurers = 0
        total_gold_transferred_to_treasury = 0

        # Fetch or create the default player
        player = db.query(Player).first()
        if not player:
            player = Player(name="Default Player", treasury=0, total_score=0)
            db.add(player)
            # Committing here to get a player ID if new, or rely on the final commit.
            # For simplicity, let's commit player creation separately if it happens.
            # Or, ensure player is part of the session and will be committed.
            # If we add to session, final db.commit() will handle it.

        for adv in adventurers:
            adventurers_processed += 1
            cost = math.floor(adv.xp * 0.01)

            if cost <= 0: # No upkeep if cost is zero or negative
                continue

            if adv.gold >= cost:
                adv.gold -= cost
                total_gold_deducted_from_adventurers += cost

                # Transfer cost to player treasury
                player.treasury += cost
                player.total_score += cost
                total_gold_transferred_to_treasury += cost

                # Ensure is_bankrupt is False if they can pay
                if adv.is_bankrupt:
                    adv.is_bankrupt = False
                    adv.expedition_status = "resting"
            else:
                # Adventurer cannot pay the full cost
                # Transfer remaining gold to treasury before setting to 0
                if adv.gold > 0:
                    player.treasury += adv.gold
                    player.total_score += adv.gold
                    total_gold_transferred_to_treasury += adv.gold
                    total_gold_deducted_from_adventurers += adv.gold # They lost this gold

                adv.gold = 0
                adv.is_bankrupt = True
                adv.expedition_status = "Bankrupt"
                bankrupt_adventurers += 1

        db.commit() # Commits changes to adventurers and the player
        return {
            "message": f"Upkeep applied for day {game_time.current_day}. "
                       f"{adventurers_processed} adventurers processed. "
                       f"{bankrupt_adventurers} became bankrupt. "
                       f"Total gold deducted from adventurers: {total_gold_deducted_from_adventurers} GP. "
                       f"Total gold transferred to player treasury: {total_gold_transferred_to_treasury} GP."
        }
    else:
        return {
            "message": f"No upkeep applied for day {game_time.current_day}. "
                       "Upkeep runs every 30 days."
        }

@app.post("/time/advance-day", response_model=GameTimeInfo)
def advance_day(db: Session = Depends(get_db)):
    """
    Advance the game time by one day.
    Initializes game time if it doesn't exist, starting at day 0, so first advance makes it day 1.
    """
    game_time = db.query(GameTime).first()

    if not game_time:
        game_time = GameTime(current_day=0, day_started_at=datetime.now(), last_updated=datetime.now())
        db.add(game_time)
        # No commit yet, will be committed after incrementing day

    game_time.current_day += 1
    game_time.last_updated = datetime.now()
    # If it was a new GameTime, day_started_at is already set.
    # If it's an existing one, day_started_at should ideally not change here,
    # unless a new day truly means resetting its start time.
    # The model sets default for day_started_at, and onupdate for last_updated.
    # For an existing game_time, current_day and last_updated are the primary changes.
    # If we want day_started_at to update ONLY when a new day occurs (not every time GameTime is touched),
    # this is a reasonable place to set it.
    # However, the model's `default=datetime.now` for `day_started_at` only applies on creation.
    # Let's ensure `day_started_at` is also updated if the day actually changes.
    # A simpler interpretation: `day_started_at` is when day 0 (or 1) started.
    # `last_updated` is when any change to GameTime happened.
    # The current model has `day_started_at` default to `datetime.now()` on creation and `last_updated` updates on any change.
    # So, for a new GameTime, both will be set. For an existing, only last_updated will auto-update via model.
    # Explicitly setting last_updated here is fine. day_started_at is fine as is upon creation.

    db.commit()
    db.refresh(game_time)

    return game_time

# --- Party Endpoints ---
@app.post("/parties/", response_model=PartyOut)
def create_party(
    name: str = Form(...),
    funds: int = Form(0),
    player_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new party from form data"""
    new_party = Party(
        name=name,
        created_at=datetime.now(),
        funds=funds,
        player_id=player_id
    )
    
    # Validate player if player_id is provided
    if player_id is not None:
        db_player = db.query(Player).filter(Player.id == player_id).first()
        if not db_player:
            raise HTTPException(status_code=404, detail="Player not found")
    
    db.add(new_party)
    db.commit()
    db.refresh(new_party)
    # Explicitly access relationships to ensure they are loaded for Pydantic
    _ = new_party.members
    _ = new_party.supplies
    return new_party

@app.get("/parties/", response_model=list[PartyOut])
def list_parties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Party).offset(skip).limit(limit).all()

@app.get("/parties/create-form", response_class=HTMLResponse)
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
    
@app.get("/parties/{party_id}/edit-form", response_class=HTMLResponse)
def party_edit_form(request: Request, party_id: int, db: Session = Depends(get_db)):
    """Return the party editing form pre-populated with party data"""
    # Fetch party and ensure it exists
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    # List all players for dropdown
    players = db.query(Player).all()
    # Get adventurers available to add (not on expedition and not already in this party)
    available_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    ).all()
    # Render enhanced form with member add UI
    return templates.TemplateResponse(
        "partials/party_form_enhanced.html",
        {
            "request": request,
            "party": party,
            "players": players,
            "available_adventurers": available_adventurers
        }
    )
    
@app.get("/parties/{party_id}/add-member-form", response_class=HTMLResponse)
def party_add_member_form(request: Request, party_id: int, db: Session = Depends(get_db)):
    """Return the add-adventurer form for a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    # Adventurers who are available and not already in this party
    available_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    ).all()
    return templates.TemplateResponse(
        "partials/add_party_member_enhanced.html",
        {"request": request, "party": party, "available_adventurers": available_adventurers}
    )
    
@app.put("/parties/{party_id}", response_model=PartyOut)
def update_party(
    party_id: int,
    name: str = Form(...),
    funds: int = Form(0),
    player_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Update party details"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    party.name = name
    party.funds = funds
    party.player_id = player_id
    db.commit()
    db.refresh(party)
    return party

@app.get("/parties/{party_id}", response_model=PartyOut)
def get_party(party_id: int, db: Session = Depends(get_db)):
    party = db.query(Party).filter(Party.id == party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    return party

@app.get("/parties/{party_id}/status")
def get_party_expedition_status(party_id: int, db: Session = Depends(get_db)):
    """Get the expedition status of a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Get current expedition if any
    current_expedition = None
    if party.on_expedition and party.current_expedition_id:
        current_expedition = db.query(Expedition).filter(
            Expedition.id == party.current_expedition_id
        ).first()
    
    # Get party member status
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

@app.post("/parties/add-member/")
def add_adventurer_to_party(
    request: Request,
    party_id: int = Form(...),
    adventurer_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Add an adventurer to a party. Returns updated form on HTMX, or JSON otherwise."""
    # Fetch party
    party = db.query(Party).filter(Party.id == party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Cannot add members to a party currently on expedition")
    # Fetch adventurer
    adventurer = db.query(Adventurer).filter(
        Adventurer.id == adventurer_id,
        Adventurer.is_available == True
    ).first()
    if adventurer is None:
        raise HTTPException(status_code=404, detail="Adventurer not found or not available")
    if adventurer in party.members:
        raise HTTPException(status_code=400, detail="Adventurer is already a member of this party")
    # Add and commit
    party.members.append(adventurer)
    db.commit()
    # On HTMX request, re-render the party edit form
    if request.headers.get("HX-Request"):
        # Return refreshed edit form in modal
        return party_edit_form(request, party.id, db)
    # Default: return JSON
    return party

@app.post("/parties/remove-member/", response_model=PartyOut)
def remove_adventurer_from_party(operation: PartyMemberOperation, db: Session = Depends(get_db)):
    # Check if party exists
    party = db.query(Party).filter(Party.id == operation.party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Check if party is on expedition
    if party.on_expedition:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove members from a party currently on expedition"
        )
    
    # Check if adventurer exists and is in the party
    adventurer = db.query(Adventurer).filter(Adventurer.id == operation.adventurer_id).first()
    if adventurer is None:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    
    # Check if adventurer is in the party
    if adventurer not in party.members:
        raise HTTPException(
            status_code=400,
            detail="Adventurer is not a member of this party"
        )
    
    # Remove adventurer from party
    party.members.remove(adventurer)
    db.commit()
    db.refresh(party)
    return party

# --- Equipment and Supply Endpoints ---
@app.post("/equipment/", response_model=EquipmentOut)
def create_equipment(equipment: EquipmentCreate, db: Session = Depends(get_db)):
    """Create a new equipment item"""
    db_equipment = Equipment(
        name=equipment.name,
        equipment_type=equipment.equipment_type,
        description=equipment.description,
        cost=equipment.cost,
        weight=equipment.weight,
        properties=equipment.properties
    )
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

@app.get("/equipment/", response_model=List[EquipmentOut])
def list_equipment(
    type_filter: Optional[EquipmentType] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """List all equipment items, optionally filtered by type"""
    query = db.query(Equipment)
    if type_filter:
        query = query.filter(Equipment.equipment_type == type_filter)
    return query.offset(skip).limit(limit).all()

@app.get("/equipment/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: int, db: Session = Depends(get_db)):
    """Get a specific equipment item by ID"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return equipment

@app.post("/adventurers/{adventurer_id}/equipment", response_model=AdventurerOut)
def add_equipment_to_adventurer(
    adventurer_id: int, 
    operation: EquipmentOperation, 
    db: Session = Depends(get_db)
):
    """Add equipment to an adventurer's inventory"""
    # Check if adventurer exists
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    
    # Check if equipment exists
    equipment = db.query(Equipment).filter(Equipment.id == operation.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Check if adventurer is on expedition
    if adventurer.on_expedition:
        raise HTTPException(
            status_code=400, 
            detail="Cannot modify equipment for adventurer currently on expedition"
        )
    
    # Check if the adventurer already has this equipment
    stmt = adventurer_equipment.select().where(
        adventurer_equipment.c.adventurer_id == adventurer_id,
        adventurer_equipment.c.equipment_id == operation.equipment_id
    )
    result = db.execute(stmt).first()
    
    if result:
        # Update existing association
        stmt = adventurer_equipment.update().where(
            adventurer_equipment.c.adventurer_id == adventurer_id,
            adventurer_equipment.c.equipment_id == operation.equipment_id
        ).values(
            quantity=result.quantity + operation.quantity
        )
        db.execute(stmt)
    else:
        # Create new association
        stmt = adventurer_equipment.insert().values(
            adventurer_id=adventurer_id,
            equipment_id=operation.equipment_id,
            quantity=operation.quantity,
            equipped=operation.equip if operation.equip is not None else False
        )
        db.execute(stmt)
    
    db.commit()
    db.refresh(adventurer)
    return adventurer

@app.put("/adventurers/{adventurer_id}/equipment/{equipment_id}/equip", response_model=AdventurerOut)
def toggle_equipment_equipped(
    adventurer_id: int, 
    equipment_id: int, 
    equip: bool = True, 
    db: Session = Depends(get_db)
):
    """Toggle whether an equipment item is equipped or not"""
    # Check if adventurer exists
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    
    # Check if adventurer is on expedition
    if adventurer.on_expedition:
        raise HTTPException(
            status_code=400, 
            detail="Cannot modify equipment for adventurer currently on expedition"
        )
    
    # Check if the adventurer has this equipment
    stmt = adventurer_equipment.select().where(
        adventurer_equipment.c.adventurer_id == adventurer_id,
        adventurer_equipment.c.equipment_id == equipment_id
    )
    result = db.execute(stmt).first()
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail="Equipment not found in adventurer's inventory"
        )
    
    # Update equipped status
    stmt = adventurer_equipment.update().where(
        adventurer_equipment.c.adventurer_id == adventurer_id,
        adventurer_equipment.c.equipment_id == equipment_id
    ).values(equipped=equip)
    db.execute(stmt)
    
    db.commit()
    db.refresh(adventurer)
    return adventurer

@app.delete("/adventurers/{adventurer_id}/equipment/{equipment_id}")
def remove_equipment_from_adventurer(
    adventurer_id: int, 
    equipment_id: int, 
    quantity: int = 1, 
    db: Session = Depends(get_db)
):
    """Remove equipment from an adventurer's inventory"""
    # Check if adventurer exists
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    
    # Check if adventurer is on expedition
    if adventurer.on_expedition:
        raise HTTPException(
            status_code=400, 
            detail="Cannot modify equipment for adventurer currently on expedition"
        )
    
    # Check if the adventurer has this equipment
    stmt = adventurer_equipment.select().where(
        adventurer_equipment.c.adventurer_id == adventurer_id,
        adventurer_equipment.c.equipment_id == equipment_id
    )
    result = db.execute(stmt).first()
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail="Equipment not found in adventurer's inventory"
        )
    
    # Update or delete based on quantity
    if result.quantity <= quantity:
        # Remove entirely
        stmt = adventurer_equipment.delete().where(
            adventurer_equipment.c.adventurer_id == adventurer_id,
            adventurer_equipment.c.equipment_id == equipment_id
        )
    else:
        # Update quantity
        stmt = adventurer_equipment.update().where(
            adventurer_equipment.c.adventurer_id == adventurer_id,
            adventurer_equipment.c.equipment_id == equipment_id
        ).values(quantity=result.quantity - quantity)
    
    db.execute(stmt)
    db.commit()
    
    return {"message": "Equipment removed successfully"}

@app.post("/supplies/", response_model=SupplyOut)
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

@app.get("/supplies/", response_model=List[SupplyOut])
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

@app.get("/supplies/{supply_id}", response_model=SupplyOut)
def get_supply(supply_id: int, db: Session = Depends(get_db)):
    """Get a specific supply item by ID"""
    supply = db.query(Supply).filter(Supply.id == supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Supply not found")
    return supply

@app.post("/parties/{party_id}/supplies", response_model=PartyOut)
def add_supply_to_party(
    party_id: int, 
    operation: SupplyOperation, 
    db: Session = Depends(get_db)
):
    """Add supplies to a party's inventory"""
    # Check if party exists
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Check if party is on expedition
    if party.on_expedition:
        raise HTTPException(
            status_code=400, 
            detail="Cannot modify supplies for party currently on expedition"
        )
    
    # Check if supply exists
    supply = db.query(Supply).filter(Supply.id == operation.supply_id).first()
    if not supply:
        raise HTTPException(status_code=404, detail="Supply not found")
    
    # Check if party has enough funds
    total_cost = supply.cost * operation.quantity
    if total_cost > party.funds:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough funds. Required: {total_cost}, Available: {party.funds}"
        )
    
    # Check if the party already has this supply
    stmt = party_supply.select().where(
        party_supply.c.party_id == party_id,
        party_supply.c.supply_id == operation.supply_id
    )
    result = db.execute(stmt).first()
    
    if result:
        # Update existing association
        stmt = party_supply.update().where(
            party_supply.c.party_id == party_id,
            party_supply.c.supply_id == operation.supply_id
        ).values(
            quantity=result.quantity + operation.quantity
        )
        db.execute(stmt)
    else:
        # Create new association
        stmt = party_supply.insert().values(
            party_id=party_id,
            supply_id=operation.supply_id,
            quantity=operation.quantity
        )
        db.execute(stmt)
    
    # Deduct funds
    party.funds -= total_cost
    
    db.commit()
    db.refresh(party)
    return party

@app.delete("/parties/{party_id}/supplies/{supply_id}")
def remove_supply_from_party(
    party_id: int, 
    supply_id: int, 
    quantity: int = 1, 
    db: Session = Depends(get_db)
):
    """Remove supplies from a party's inventory"""
    # Check if party exists
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Check if party is on expedition
    if party.on_expedition:
        raise HTTPException(
            status_code=400, 
            detail="Cannot modify supplies for party currently on expedition"
        )
    
    # Check if the party has this supply
    stmt = party_supply.select().where(
        party_supply.c.party_id == party_id,
        party_supply.c.supply_id == supply_id
    )
    result = db.execute(stmt).first()
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail="Supply not found in party's inventory"
        )
    
    # Update or delete based on quantity
    if result.quantity <= quantity:
        # Remove entirely
        stmt = party_supply.delete().where(
            party_supply.c.party_id == party_id,
            party_supply.c.supply_id == supply_id
        )
    else:
        # Update quantity
        stmt = party_supply.update().where(
            party_supply.c.party_id == party_id,
            party_supply.c.supply_id == supply_id
        ).values(quantity=result.quantity - quantity)
    
    db.execute(stmt)
    db.commit()
    
    return {"message": "Supply removed successfully"}

@app.put("/parties/{party_id}/funds", response_model=PartyOut)
def update_party_funds(
    party_id: int, 
    funds_update: PartyFundsUpdate, 
    db: Session = Depends(get_db)
):
    """Update a party's funds (add or remove gold)"""
    # Check if party exists
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # If removing funds, check if party has enough
    if funds_update.amount < 0 and abs(funds_update.amount) > party.funds:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough funds. Attempting to remove {abs(funds_update.amount)}, Available: {party.funds}"
        )
    
    # Update funds
    party.funds += funds_update.amount
    
    db.commit()
    db.refresh(party)
    return party

# Create shared simulator instance
simulator = DungeonSimulator()

# --- Expedition Endpoints ---
# Note: Specific routes must come before parameterized routes
@app.get("/expeditions/active", response_class=HTMLResponse)
def expeditions_active(request: Request, db: Session = Depends(get_db)):
    """Get active expeditions partial"""
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    
    # Get game time for progress calculations
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    return templates.TemplateResponse(
        "partials/active_expeditions.html",
        {
            "request": request,
            "active_expeditions": active_expeditions,
            "game_time": game_time
        }
    )

@app.get("/expeditions/completed", response_class=HTMLResponse)
def expeditions_completed(request: Request, db: Session = Depends(get_db)):
    """Get completed expeditions partial"""
    completed_expeditions = db.query(Expedition).filter(
        Expedition.result == "completed"
    ).order_by(Expedition.finished_at.desc()).limit(10).all()
    
    return templates.TemplateResponse(
        "partials/completed_expeditions.html",
        {
            "request": request,
            "completed_expeditions": completed_expeditions
        }
    )

@app.get("/expeditions/create-form", response_class=HTMLResponse)
def expedition_create_form(request: Request, party_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Return the expedition creation form"""
    try:
        # Get all available parties (not on expedition)
        parties = db.query(Party).filter(Party.on_expedition == False).all()
        
        # Get selected party if provided
        selected_party = None
        if party_id:
            selected_party = db.query(Party).filter(Party.id == party_id).first()
        
        # Get treasury total from the first player for header display
        treasury_gold = 0
        player = db.query(Player).first()
        if player:
            treasury_gold = player.treasury
        
        return templates.TemplateResponse(
            "partials/expedition_form.html",
            {
                "request": request,
                "parties": parties,
                "party": selected_party,
                "treasury_gold": treasury_gold
            }
        )
    except Exception as e:
        print(f"Error in expedition_create_form: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/expeditions/new", response_class=HTMLResponse)
def expeditions_new_redirect(request: Request, db: Session = Depends(get_db)):
    """Redirect to expeditions page (legacy route)"""
    return expeditions_page(request, db)

@app.post("/expeditions/", response_model=ExpeditionResult)
def launch_expedition(
    party_id: int = Form(...),
    dungeon_level: int = Form(...),
    db: Session = Depends(get_db)
):
    """Launch a new expedition with a party to a dungeon"""
    duration_days = 7
    # Create ExpeditionCreate object
    expedition_data = ExpeditionCreate(
        party_id=party_id,
        dungeon_level=dungeon_level,
        duration_days=duration_days,
        supplies_to_bring=[]  # Setting to empty list as per requirement
    )

    # Check if party exists
    party = db.query(Party).filter(Party.id == expedition_data.party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Check if party has members
    if not party.members:
        raise HTTPException(status_code=400, detail="Party has no members")
    
    # Check if party is already on an expedition
    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Party is already on an expedition")

    # Check for bankrupt members
    for member in party.members:
        if member.is_bankrupt:
            raise HTTPException(
                status_code=400,
                detail=f"Party contains bankrupt members who cannot go on expeditions. Member: {member.name} is bankrupt."
            )
    
    # Process supplies to bring on expedition
    supplies_to_bring = {}
    if expedition_data.supplies_to_bring:
        for supply_data in expedition_data.supplies_to_bring:
            for supply_id_str, quantity in supply_data.items():
                try:
                    supply_id = int(supply_id_str)
                    # Verify supply exists and party has enough
                    stmt = party_supply.select().where(
                        party_supply.c.party_id == party.id,
                        party_supply.c.supply_id == supply_id
                    )
                    result = db.execute(stmt).first()
                    
                    if not result:
                        supply = db.query(Supply).filter(Supply.id == supply_id).first()
                        if not supply:
                            raise HTTPException(
                                status_code=404, 
                                detail=f"Supply with ID {supply_id} not found"
                            )
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Party does not have supply: {supply.name}"
                        )
                    
                    if result.quantity < quantity:
                        supply = db.query(Supply).filter(Supply.id == supply_id).first()
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Not enough {supply.name}, have {result.quantity}, requested {quantity}"
                        )
                    
                    supplies_to_bring[supply_id] = quantity
                except ValueError:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid supply ID: {supply_id_str}"
                    )
    
    # Convert party to format needed for simulator
    party_members = []
    for member in party.members:
        # Get equipment for member
        equipment_list = []
        for assoc in db.query(adventurer_equipment).filter(
            adventurer_equipment.c.adventurer_id == member.id,
            adventurer_equipment.c.equipped == True
        ).all():
            equipment = db.query(Equipment).filter(Equipment.id == assoc.equipment_id).first()
            if equipment:
                equipment_list.append({
                    "id": equipment.id,
                    "name": equipment.name,
                    "type": equipment.equipment_type.value,
                    "properties": equipment.properties or {}
                })
        
        party_members.append({
            "id": member.id,
            "name": member.name,
            "character_class": member.adventurer_class.value,
            "level": member.level,
            "hit_points": member.hp_max,
            "current_hp": member.hp_current,
            "xp": member.xp,
            "equipment": equipment_list
        })
    
    # Add party to simulator if not already there
    # party_id is already defined from Form input
    simulator_party_idx = None
    # Ensure party_members is not empty before accessing its elements
    if party_members:
        for idx, sim_party in enumerate(simulator.parties):
            if len(sim_party) > 0 and sim_party[0].get("id") == party_members[0].get("id"):
                simulator_party_idx = idx
                break
    
    if simulator_party_idx is None:
        simulator_party_idx = simulator.add_party(party_members)
    
    # Start expedition in simulator
    expedition_id_sim = simulator.start_expedition( # Renamed to avoid conflict with DB expedition_id
        simulator_party_idx, 
        dungeon_level=expedition_data.dungeon_level
    )
    
    # Get or create game time to set expedition days
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    # Create expedition record in database
    start_day = game_time.current_day
    # duration_days is now defined at the start of the function
    return_day = start_day + duration_days
    
    db_expedition = Expedition(
        party_id=expedition_data.party_id, # Use party_id from expedition_data
        start_day=start_day,
        duration_days=duration_days, # Use the new duration_days variable
        return_day=return_day,
        started_at=datetime.now(),
        result="in_progress",
        supplies_consumed={},  # Will be populated after expedition
        equipment_lost={}  # Will be populated after expedition
    )
    db.add(db_expedition)
    db.commit()
    db.refresh(db_expedition)
    
    # Update party status to on expedition
    party.on_expedition = True
    party.current_expedition_id = db_expedition.id
    
    # Update all adventurers in the party
    for member in party.members:
        member.on_expedition = True
        member.expedition_status = "active"
        member.is_available = False
    
    # Consume supplies brought on expedition (remove from inventory)
    supplies_consumed = {}
    for supply_id, quantity in supplies_to_bring.items():
        # Get supply info
        supply = db.query(Supply).filter(Supply.id == supply_id).first()
        if supply:
            # Record for expedition result
            supplies_consumed[supply.name] = quantity
            
            # Update party's supply inventory
            stmt = party_supply.update().where(
                party_supply.c.party_id == party.id,
                party_supply.c.supply_id == supply_id
            ).values(
                quantity=party_supply.c.quantity - quantity
            )
            db.execute(stmt)
    
    db.commit()
    
    # Run expedition to completion
    result = simulator.run_expedition_to_completion(expedition_id_sim)
    
    # Update expedition in database
    db_expedition.finished_at = datetime.now()
    db_expedition.result = "completed"
    db_expedition.supplies_consumed = supplies_consumed
    
    # Handle potential equipment loss during expedition
    # For this implementation, we'll have a 5% chance per adventurer to lose one equipped item
    equipment_lost = {}
    for member in party.members:
        import random
        if random.random() < 0.05:  # 5% chance to lose equipment
            # Get one random equipped item
            stmt = adventurer_equipment.select().where(
                adventurer_equipment.c.adventurer_id == member.id,
                adventurer_equipment.c.equipped == True
            )
            equipped_items = list(db.execute(stmt).all())
            
            if equipped_items:
                lost_item = random.choice(equipped_items)
                equipment = db.query(Equipment).filter(Equipment.id == lost_item.equipment_id).first()
                
                if equipment:
                    # Record the loss for the expedition
                    if member.name not in equipment_lost:
                        equipment_lost[member.name] = []
                    equipment_lost[member.name].append(equipment.name)
                    
                    # Remove the equipment from the adventurer
                    if lost_item.quantity <= 1:
                        # Remove entirely
                        stmt = adventurer_equipment.delete().where(
                            adventurer_equipment.c.adventurer_id == member.id,
                            adventurer_equipment.c.equipment_id == lost_item.equipment_id
                        )
                    else:
                        # Update quantity
                        stmt = adventurer_equipment.update().where(
                            adventurer_equipment.c.adventurer_id == member.id,
                            adventurer_equipment.c.equipment_id == lost_item.equipment_id
                        ).values(quantity=lost_item.quantity - 1)
                    
                    db.execute(stmt)
    
    db_expedition.equipment_lost = equipment_lost
    
    # Reset party expedition status
    party.on_expedition = False
    party.current_expedition_id = None
    
    # Store the detailed results as JSON in the log field
    for node_result in result["log"]:
        exp_node = ExpeditionNodeResult(
            expedition_id=db_expedition.id,
            node_id=1,  # Default node for now
            success=True,
            xp_earned=int(result["xp_earned"] / len(result["log"])),
            loot=int(result["treasure_total"] / len(result["log"])),
            log=json.dumps(node_result)
        )
        db.add(exp_node)
    
    # Store individual adventurer logs
    for member in party.members:
        is_dead = member.name in result["dead_members"]
        log = ExpeditionLog(
            expedition_id=db_expedition.id,
            adventurer_id=member.id,
            xp_share=int(result["xp_per_party_member"]),
            hp_change=-10 if is_dead else -5,  # Simplified HP loss
            status="dead" if is_dead else "alive"
        )
        db.add(log)
        
        # Update adventurer stats
        member.xp += int(result["xp_per_party_member"])
        
        if is_dead:
            member.hp_current = 1  # Reduced to 1 HP if dead
            member.expedition_status = "injured"
        else:
            member.hp_current = max(1, member.hp_current - 5)  # Some HP loss
            member.expedition_status = "resting"
        
        # Reset expedition status but keep availability restricted for recovery period
        member.on_expedition = False
        member.is_available = member.hp_current > (member.hp_max / 2)  # Only available if over half health
    
    # Calculate loot split (70% to party/adventurers, 30% to player treasury)
    total_loot = result["treasure_total"]
    party_size = len(party.members)
    
    # Use the loot split calculation function
    loot_split = calculate_loot_split(total_loot, party_size, player_split=0.3)
    
    # Add adventurers' share to party funds
    party.funds += loot_split["adventurers_share"]
    
    # Add treasury share to player if party is associated with a player
    if party.player_id:
        player = db.query(Player).filter(Player.id == party.player_id).first()
        if player:
            # Add to player's treasury
            player.treasury += loot_split["player_treasury"]
            # Add to total score (keeps track of all gold ever collected)
            player.total_score += loot_split["player_treasury"]
            
    # Update individual adventurer gold amounts
    if loot_split["individual_share"] > 0:
        for member in party.members:
            member.gold += loot_split["individual_share"]
    
    # Add the loot split information to the result
    result["loot_split"] = loot_split
            
    db.commit()
    
    # Add supplies and equipment info to the result
    result["supplies_consumed"] = supplies_consumed
    result["equipment_lost"] = equipment_lost
    
    # Return full expedition results
    return result

@app.get("/expeditions/{expedition_id}/details", response_class=HTMLResponse)
def expedition_details_page(request: Request, expedition_id: int, db: Session = Depends(get_db)):
    """Render the expedition details page"""
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")

    node_results = db.query(ExpeditionNodeResult).filter(ExpeditionNodeResult.expedition_id == expedition_id).all()

    processed_logs = []
    total_loot = 0
    total_xp = 0

    for node in node_results:
        try:
            log_data = json.loads(node.log)
            processed_logs.append({"log_data": log_data}) # Match template variable
        except (json.JSONDecodeError, TypeError):
            processed_logs.append({"log_data": {"error": "Could not parse log entry."}})
        total_loot += node.loot or 0
        total_xp += node.xp_earned or 0

    # Get player treasury for base template
    player = db.query(Player).first()
    treasury_gold = player.treasury if player else 0

    return templates.TemplateResponse(
        "expedition_details.html",
        {
            "request": request,
            "expedition": expedition,
            "expedition_logs": processed_logs,
            "total_loot": total_loot,
            "total_xp": total_xp,
            "treasury_gold": treasury_gold,
        }
    )

@app.get("/expeditions/{expedition_id}", response_model=ExpeditionResult)
def get_expedition_results(expedition_id: int, db: Session = Depends(get_db)):
    """Get detailed results of an expedition"""
    # First, check if the expedition exists in the database
    db_expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not db_expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    try:
        # Try to get results from simulator
        result = simulator.get_expedition_results(expedition_id)
        
        # Add level-up eligibility for party members
        if "party_members_ready_for_level_up" not in result:
            # Get party and check for members who can level up
            party = db.query(Party).filter(Party.id == db_expedition.party_id).first()
            if party:
                members_ready = []
                for member in party.members:
                    if check_for_level_up(member.level, member.xp):
                        members_ready.append({
                            "id": member.id,
                            "name": member.name,
                            "current_level": member.level,
                            "next_level": member.level + 1
                        })
                result["party_members_ready_for_level_up"] = members_ready
        
        return result
    except ValueError:
        # If not in simulator, create a response from database records
        party = db.query(Party).filter(Party.id == db_expedition.party_id).first()
        node_results = db.query(ExpeditionNodeResult).filter(
            ExpeditionNodeResult.expedition_id == expedition_id
        ).all()
        expedition_logs = db.query(ExpeditionLog).filter(
            ExpeditionLog.expedition_id == expedition_id
        ).all()
        
        # Construct log from node results
        log = []
        for node in node_results:
            try:
                turn_log = json.loads(node.log)
                log.append(turn_log)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Construct status
        party_status = {
            "members_total": len(party.members) if party else 0,
            "members_alive": len([m for m in party.members if m.hp_current > 0]) if party else 0,
            "members_dead": len([log for log in expedition_logs if log.status == "dead"]),
            "hp_current": sum(m.hp_current for m in party.members) if party else 0,
            "hp_max": sum(m.hp_max for m in party.members) if party else 0,
            "hp_percentage": (sum(m.hp_current for m in party.members) / 
                             sum(m.hp_max for m in party.members)) * 100 if party and sum(m.hp_max for m in party.members) > 0 else 0
        }
        
        # Check which party members can level up
        members_ready_for_level_up = []
        if party:
            for member in party.members:
                if check_for_level_up(member.level, member.xp):
                    members_ready_for_level_up.append({
                        "id": member.id,
                        "name": member.name,
                        "current_level": member.level,
                        "next_level": member.level + 1
                    })
        
        # Create a result object
        result = {
            "expedition_id": expedition_id,
            "party_id": db_expedition.party_id,
            "dungeon_level": 1,  # Default
            "turns": len(node_results),
            "start_time": db_expedition.started_at,
            "end_time": db_expedition.finished_at,
            "start_day": db_expedition.start_day,
            "duration_days": db_expedition.duration_days,
            "return_day": db_expedition.return_day,
            "treasure_total": sum(node.loot for node in node_results),
            "special_items": [],
            "xp_earned": sum(node.xp_earned for node in node_results),
            "xp_per_party_member": sum(node.xp_earned for node in node_results) / max(1, len(party.members)) if party else 0,
            "resources_used": {"hp_lost": 0, "spells_used": 0, "supplies_used": 0},
            "dead_members": [log.adventurer.name for log in expedition_logs if log.status == "dead"],
            "party_status": party_status,
            "log": log,
            "party_members_ready_for_level_up": members_ready_for_level_up
        }
        
        return result

@app.get("/expeditions/", response_model=list)
def list_expeditions(db: Session = Depends(get_db)):
    """List all expeditions in the database"""
    return db.query(Expedition).all()

@app.post("/expeditions/{expedition_id}/advance", response_model=TurnResult)
def advance_expedition_turn(expedition_id: int, db: Session = Depends(get_db)):
    """Advance an expedition by one turn"""
    # Check if expedition exists in database
    db_expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not db_expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    # Check if expedition is still in progress
    if db_expedition.result != "in_progress":
        raise HTTPException(status_code=400, detail="Expedition is already completed")
    
    try:
        # Advance turn in simulator
        result = simulator.advance_turn(expedition_id)
        
        # Update expedition status in database
        if result["expedition_ended"]:
            db_expedition.result = "completed"
            db_expedition.finished_at = datetime.now()
            
            # Get the party
            party = db.query(Party).filter(Party.id == db_expedition.party_id).first()
            if party:
                party.on_expedition = False
                party.current_expedition_id = None
                
                # Update adventurers' status
                for member in party.members:
                    member.on_expedition = False
                    
                    # Set status based on health
                    if member.hp_current <= 1:
                        member.expedition_status = "injured"
                    else:
                        member.expedition_status = "resting"
                    
                    # Update availability based on health
                    member.is_available = member.hp_current > (member.hp_max / 2)
            
            db.commit()
            
        # Record turn result in database
        exp_node = ExpeditionNodeResult(
            expedition_id=db_expedition.id,
            node_id=1,  # Default node for now
            success=True,
            xp_earned=sum(event.get("xp_earned", 0) for event in result["events"]) if "events" in result else 0,
            loot=sum(event.get("treasure", {}).get("gold", 0) for event in result["events"] if "treasure" in event) if "events" in result else 0,
            log=json.dumps(result)
        )
        db.add(exp_node)
        db.commit()
        
        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Expedition not found in simulator")

# --- Time Endpoints ---
@app.post("/time/advance-day", response_class=HTMLResponse)
def advance_day(request: Request, db: Session = Depends(get_db)):
    """Advances the game time by one day and updates expedition statuses."""
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        # db.commit() # Commit will happen after updates
        # db.refresh(game_time)

    game_time.current_day += 1

    # Process expedition completions
    active_expeditions_to_check = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    for expedition in active_expeditions_to_check:
        if expedition.return_day <= game_time.current_day:
            expedition.result = "completed"
            expedition.finished_at = datetime.now()

            if expedition.party:
                expedition.party.on_expedition = False
                for adventurer in expedition.party.members:
                    adventurer.on_expedition = False
                    adventurer.is_available = True # Simple availability, can be refined
                    # Potentially reset expedition_status here too if needed
                    # adventurer.expedition_status = "idle"

    db.commit() # Commit all changes: game_time increment and expedition updates

    # Fetch updated active expeditions to return the partial
    updated_active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()

    # Get treasury for the partial
    player = db.query(Player).first()
    treasury_gold = player.treasury if player else 0

    return templates.TemplateResponse(
        "partials/active_expeditions.html",
        {
            "request": request,
            "active_expeditions": updated_active_expeditions,
            "game_time": game_time,
            "treasury_gold": treasury_gold
        }
    )

# --- Frontend Routes ---
@app.get("/expeditions", response_class=HTMLResponse)
def expeditions_page(request: Request, db: Session = Depends(get_db)):
    """Render the expeditions page"""
    # Get active expeditions (in progress)
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    
    # Get GameTime
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit() # Commit if new game time is created
        db.refresh(game_time)

    # Get treasury total from the first player for header display
    player = db.query(Player).first()
    treasury_gold = player.treasury if player else 0
    
    return templates.TemplateResponse(
        "expeditions.html",
        {
            "request": request,
            "active_expeditions": active_expeditions,
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/expeditions/new", response_class=HTMLResponse)
def expeditions_new_redirect(request: Request, db: Session = Depends(get_db)):
    """Redirect to expeditions page (legacy route)"""
    return expeditions_page(request, db)

@app.get("/expeditions/create-form", response_class=HTMLResponse)
def expedition_create_form(request: Request, party_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """Return the expedition creation form"""
    try:
        # Get all available parties (not on expedition)
        parties = db.query(Party).filter(Party.on_expedition == False).all()
        
        # Get selected party if provided
        selected_party = None
        if party_id:
            selected_party = db.query(Party).filter(Party.id == party_id).first()
        
        # Get treasury total from the first player for header display
        treasury_gold = 0
        player = db.query(Player).first()
        if player:
            treasury_gold = player.treasury
        
        return templates.TemplateResponse(
            "partials/expedition_form.html",
            {
                "request": request,
                "parties": parties,
                "party": selected_party,
                "treasury_gold": treasury_gold
            }
        )
    except Exception as e:
        print(f"Error in expedition_create_form: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    """Render the home page"""
    adventurer_count = db.query(Adventurer).count()
    party_count = db.query(Party).count()
    expedition_count = db.query(Expedition).count()
    
    # Get recent expeditions
    recent_expeditions = db.query(Expedition).order_by(Expedition.started_at.desc()).limit(5).all()
    
    # Get player treasury (use first player for now, or create one if none exists)
    player = db.query(Player).first()
    if not player:
        player = Player(name="Default Player", treasury=0, total_score=0)
        db.add(player)
        db.commit()
        db.refresh(player)
    # Get or create game time record
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    # Compute active expeditions (in progress)
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    # Compute unavailable adventurers count
    unavailable_adventurers = db.query(Adventurer).filter(Adventurer.is_available == False).count()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "adventurer_count": adventurer_count,
            "party_count": party_count,
            "expedition_count": expedition_count,
            "recent_expeditions": recent_expeditions,
            "treasury_gold": player.treasury,
            "total_score": player.total_score,
            "game_time": game_time,
            "active_expeditions": active_expeditions,
            "unavailable_adventurers": unavailable_adventurers
        }
    )

@app.get("/adventurers", response_class=HTMLResponse)
def adventurers_page(request: Request, db: Session = Depends(get_db)):
    """Render the adventurers page"""
    adventurers = db.query(Adventurer).all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "adventurers.html", 
        {"request": request, "adventurers": adventurers, "treasury_gold": treasury_gold}
    )

@app.get("/adventurers/create-form", response_class=HTMLResponse)
def adventurer_create_form(request: Request, db: Session = Depends(get_db)):
    """Return the adventurer creation form"""
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "partials/adventurer_form.html", 
        {"request": request, "treasury_gold": treasury_gold}
    )
    
@app.get("/parties", response_class=HTMLResponse)
def parties_page(request: Request, db: Session = Depends(get_db)):
    """Render the parties page"""
    parties = db.query(Party).all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Get game time
    game_time = db.query(GameTime).first()
    
    return templates.TemplateResponse(
        "parties.html", 
        {
            "request": request, 
            "parties": parties, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/ui/get-party-list", response_class=HTMLResponse)
def get_party_list_html(
    request: Request, 
    filter_type: Optional[str] = "all",
    sort_by: Optional[str] = "name",
    db: Session = Depends(get_db)
):
    """Get HTML partial for the party list, with optional filtering and sorting."""
    query = db.query(Party)
    
    # Apply filters
    if filter_type == "available":
        query = query.filter(Party.on_expedition == False)
    elif filter_type == "expedition":
        query = query.filter(Party.on_expedition == True)
    
    # Apply sorting
    if sort_by == "members":
        # Using a subquery to count members since we can't sort directly by relationship length
        from sqlalchemy import func
        member_count = db.query(
            party_adventurer.c.party_id, 
            func.count(party_adventurer.c.adventurer_id).label('member_count')
        ).group_by(party_adventurer.c.party_id).subquery()
        
        # Join with the subquery and order by the count
        query = query.outerjoin(
            member_count, 
            Party.id == member_count.c.party_id
        ).order_by(member_count.c.member_count.desc(), Party.name)
    elif sort_by == "funds":
        query = query.order_by(Party.funds.desc(), Party.name)
    else:  # Default sort by name
        query = query.order_by(Party.name)
    
    parties = query.all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Get game time
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

@app.get("/parties/sort", response_class=HTMLResponse)
def sort_parties(
    request: Request, 
    sort_by: Optional[str] = "name",
    filter_type: Optional[str] = "all",
    db: Session = Depends(get_db)
):
    """Sort parties by different criteria"""
    return filter_parties(request, filter_type, sort_by, db)

@app.get("/parties/{party_id}/filter-adventurers", response_class=HTMLResponse)
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
    
    # Base query: available adventurers not in this party
    query = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    )
    
    # Apply class filter
    if class_filter and class_filter != "":
        query = query.filter(Adventurer.adventurer_class == class_filter)
    
    # Apply level filter
    if level_filter and level_filter != "":
        min_level = int(level_filter)
        query = query.filter(Adventurer.level >= min_level)
    
    # Sort by level and then name
    available_adventurers = query.order_by(Adventurer.level.desc(), Adventurer.name).all()
    
    # Add progression data
    available_adventurers = [add_progression_data(adv) for adv in available_adventurers]
    
    # Get game time for healing days display
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

@app.get("/parties/{party_id}/supplies", response_class=HTMLResponse)
def party_supplies(
    request: Request,
    party_id: int,
    type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Show and manage party supplies"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Get all supply types for the filter
    supply_types = list(SupplyType)
    
    # Query for available supplies to purchase
    query = db.query(Supply)
    
    # Filter by type if specified
    if type:
        query = query.filter(Supply.supply_type == type)
    
    # Get all available supplies
    available_supplies = query.order_by(Supply.supply_type, Supply.cost, Supply.name).all()
    
    # Get treasury total from the first player for header display
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

@app.get("/parties/{party_id}/add-funds-form", response_class=HTMLResponse)
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
        {
            "request": request, 
            "party": party,
            "action": "add"
        }
    )

@app.get("/parties/{party_id}/remove-funds-form", response_class=HTMLResponse)
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
        {
            "request": request, 
            "party": party,
            "action": "remove"
        }
    )