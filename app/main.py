from fastapi import FastAPI, HTTPException, Depends, Body, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import json

from app.models import (
    Base, Adventurer, Party, DungeonNode, Expedition, 
    ExpeditionNodeResult, ExpeditionLog, Equipment, Supply,
    EquipmentType, SupplyType, adventurer_equipment, party_supply,
    Player, GameTime
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

# Initialize game time if not exists
def initialize_database():
    db = SessionLocal()
    try:
        # Check if we need to initialize game time
        game_time = db.query(GameTime).first()
        if not game_time:
            game_time = GameTime()
            db.add(game_time)
            db.commit()
        
        # Update existing expeditions if they don't have time data
        expeditions = db.query(Expedition).all()
        for expedition in expeditions:
            if not hasattr(expedition, 'start_day') or expedition.start_day is None:
                expedition.start_day = game_time.current_day
                expedition.duration_days = 7
                expedition.return_day = game_time.current_day + 7
        
        db.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        db.close()

# Initialize database on startup
initialize_database()

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

@app.get("/adventurers/{adventurer_id}/data", response_model=AdventurerOut)
def get_adventurer_data(adventurer_id: int, db: Session = Depends(get_db)):
    """Get a specific adventurer data by ID (JSON API endpoint)"""
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

# --- Party Endpoints ---
@app.post("/parties/", response_model=PartyOut)
def create_party(party: PartyCreate, db: Session = Depends(get_db)):
    new_party = Party(
        name=party.name,
        created_at=datetime.now(),
        funds=party.funds,
        player_id=party.player_id
    )
    
    # Validate player if player_id is provided
    if party.player_id:
        player = db.query(Player).filter(Player.id == party.player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
    
    db.add(new_party)
    db.commit()
    db.refresh(new_party)
    return new_party

@app.get("/parties/", response_model=list[PartyOut])
def list_parties(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Party).offset(skip).limit(limit).all()

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

@app.post("/parties/add-member/", response_model=PartyOut)
def add_adventurer_to_party(operation: PartyMemberOperation, db: Session = Depends(get_db)):
    # Check if party exists
    party = db.query(Party).filter(Party.id == operation.party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Check if party is on expedition
    if party.on_expedition:
        raise HTTPException(
            status_code=400,
            detail="Cannot add members to a party currently on expedition"
        )
    
    # Check if adventurer exists and is available
    adventurer = db.query(Adventurer).filter(
        Adventurer.id == operation.adventurer_id,
        Adventurer.is_available == True
    ).first()
    if adventurer is None:
        raise HTTPException(
            status_code=404, 
            detail="Adventurer not found or not available"
        )
    
    # Check if adventurer is already in this party
    if adventurer in party.members:
        raise HTTPException(
            status_code=400,
            detail="Adventurer is already a member of this party"
        )
    
    # Add adventurer to party
    party.members.append(adventurer)
    db.commit()
    db.refresh(party)
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

# --- Game Time Endpoints ---
@app.get("/time/", response_model=GameTimeInfo)
def get_game_time(db: Session = Depends(get_db)):
    """Get the current game time"""
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    return game_time

@app.post("/time/advance/", response_class=HTMLResponse)
def advance_game_time(request: Request,
                      days: int = Form(1),
                      db: Session = Depends(get_db)):
    """Advance the game time by a specified number of days"""
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    old_day = game_time.current_day
    game_time.current_day += days
    game_time.last_updated = datetime.now()
    
    # Check all expeditions if they have returned
    check_returning_expeditions(old_day, game_time.current_day, db)
    
    db.commit()
    db.refresh(game_time)
    
    # Count expeditions returned today for UI feedback
    expeditions_returned = process_returns(db)
    
    # Get updated data for the time panel
    active_expeditions = db.query(Expedition).filter(
        Expedition.result == "in_progress"
    ).all()
    
    unavailable_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == False,
        Adventurer.on_expedition == False
    ).count()
    
    # Get healing adventurers to display
    healing_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == False,
        Adventurer.on_expedition == False,
        Adventurer.expedition_status.in_(["healing", "injured"])
    ).all()
    
    # Return updated time panel HTML
    return templates.TemplateResponse(
        "partials/time_panel.html", 
        {
            "request": request,
            "game_time": game_time,
            "active_expeditions": active_expeditions,
            "unavailable_adventurers": unavailable_adventurers,
            "expeditions_returned": expeditions_returned,
            "healing_adventurers": healing_adventurers
        }
    )

def check_returning_expeditions(old_day: int, new_day: int, db: Session):
    """Check if any expeditions should return between the old and new days"""
    # Find all in-progress expeditions that should return within the time span
    returning_expeditions = db.query(Expedition).filter(
        Expedition.result == "in_progress",
        Expedition.return_day > old_day,
        Expedition.return_day <= new_day
    ).all()
    
    for expedition in returning_expeditions:
        process_expedition_return(expedition, db)

def process_expedition_return(expedition: Expedition, db: Session):
    """Process the return of an expedition"""
    # Set expedition as completed
    expedition.result = "completed"
    expedition.finished_at = datetime.now()
    
    # Get the party
    party = db.query(Party).filter(Party.id == expedition.party_id).first()
    if party:
        # Update party status
        party.on_expedition = False
        party.current_expedition_id = None
        
        # Update all adventurers in the party
        for member in party.members:
            member.on_expedition = False
            # Set the adventurer status based on health
            if member.hp_current <= member.hp_max * 0.3:
                member.expedition_status = "injured"
                member.is_available = False
            else:
                member.expedition_status = "resting"
                member.is_available = True
    
    # Run the expedition in the simulator to generate results
    # This is a simplified version - the real implementation would have proper results generation
    result = simulator.run_expedition_to_completion(expedition.id)
    
    # Apply expedition results (treasure, XP, etc.)
    apply_expedition_results(expedition.id, result, db)
    
    db.commit()

def apply_expedition_results(expedition_id: int, result: dict, db: Session):
    """Apply the results of a completed expedition"""
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not expedition:
        return
    
    party = db.query(Party).filter(Party.id == expedition.party_id).first()
    if not party:
        return
    
    # Process loot and XP
    # This is simplified - real implementation would have more detailed processing
    total_loot = result.get("treasure_total", 0)
    xp_earned = result.get("xp_earned", 0)
    
    # Calculate loot splits (player gets 30%, party gets 70%)
    loot_split = calculate_loot_split(total_loot, len(party.members), player_split=0.3)
    
    # Update party funds
    party.funds += loot_split["adventurers_share"]
    
    # Update player treasury if party has a player
    if party.player_id:
        player = db.query(Player).filter(Player.id == party.player_id).first()
        if player:
            player.treasury += loot_split["player_treasury"]
            player.total_score += loot_split["player_treasury"]
    
    # Update adventurers
    # Get current game day for healing calculations
    game_time = db.query(GameTime).first()
    current_day = game_time.current_day if game_time else 1
    
    xp_per_member = xp_earned // max(1, len(party.members))
    for member in party.members:
        member.xp += xp_per_member
        member.gold += loot_split["individual_share"]
        
        # Handle injuries - simplified version
        if member.name in result.get("dead_members", []):
            member.hp_current = 1  # Nearly dead, needs healing
            member.expedition_status = "injured"
            member.is_available = False
            
            # Calculate healing time (2 days per HP needed to recover)
            hp_to_recover = member.hp_max - member.hp_current
            healing_days = hp_to_recover * 2
            member.healing_until_day = current_day + healing_days
        else:
            # Some damage from expedition
            hp_loss = min(member.hp_current - 1, int(member.hp_max * 0.3))
            member.hp_current -= hp_loss
            
            # If adventurer took damage, enter healing state
            if hp_loss > 0:
                # Calculate days needed to heal (2 days per HP)
                hp_to_recover = member.hp_max - member.hp_current
                healing_days = hp_to_recover * 2
                
                # Set healing status and completion day
                member.expedition_status = "healing"
                member.healing_until_day = current_day + healing_days
                member.is_available = False
            else:
                # No damage taken, adventurer is available
                member.expedition_status = "available"
                member.is_available = True

def process_returns(db: Session):
    """Check for and process any expeditions that should return today"""
    game_time = db.query(GameTime).first()
    if not game_time:
        return 0
        
    # Find expeditions that should return today
    returning_expeditions = db.query(Expedition).filter(
        Expedition.result == "in_progress",
        Expedition.return_day == game_time.current_day
    ).all()
    
    for expedition in returning_expeditions:
        process_expedition_return(expedition, db)
    
    return len(returning_expeditions)

@app.post("/time/skip-until-ready", response_class=HTMLResponse)
def skip_until_ready(request: Request, db: Session = Depends(get_db)):
    """Skip time until all expeditions have returned and all adventurers are available"""
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    # Get the farthest return date of any expedition
    farthest_expedition = db.query(Expedition).filter(
        Expedition.result == "in_progress"
    ).order_by(Expedition.return_day.desc()).first()
    
    # Check if we have any expeditions to wait for
    days_to_advance = 0
    expeditions_returned = 0
    
    if farthest_expedition:
        days_to_advance = max(0, farthest_expedition.return_day - game_time.current_day)
    
    # If no expeditions but we have resting adventurers, skip a week to heal them
    if days_to_advance == 0:
        unavailable_adventurers = db.query(Adventurer).filter(
            Adventurer.is_available == False,
            Adventurer.on_expedition == False
        ).count()
        
        if unavailable_adventurers > 0:
            days_to_advance = 7  # Advance a week to heal adventurers
    
    # If anything to advance, do so
    if days_to_advance > 0:
        old_day = game_time.current_day
        game_time.current_day += days_to_advance
        game_time.last_updated = datetime.now()
        
        # Check expeditions that have returned
        check_returning_expeditions(old_day, game_time.current_day, db)
        expeditions_returned = process_returns(db)
        
        # Make resting/healing adventurers available if they've completed healing
        resting_adventurers = db.query(Adventurer).filter(
            Adventurer.is_available == False,
            Adventurer.on_expedition == False
        ).all()
        
        for adventurer in resting_adventurers:
            if adventurer.expedition_status == "healing" and adventurer.healing_until_day:
                # Check if the healing period is complete
                if game_time.current_day >= adventurer.healing_until_day:
                    # Healing period complete, restore to full health
                    adventurer.hp_current = adventurer.hp_max
                    adventurer.expedition_status = "available"
                    adventurer.is_available = True
                    adventurer.healing_until_day = None
                else:
                    # Still healing, calculate progress based on days passed
                    days_healing = min(days_to_advance, adventurer.healing_until_day - (game_time.current_day - days_to_advance))
                    hp_to_recover = adventurer.hp_max - adventurer.hp_current
                    hp_recovery = min(hp_to_recover, days_healing // 2)  # 1 HP per 2 days
                    
                    if hp_recovery > 0:
                        adventurer.hp_current += hp_recovery
            else:
                # Legacy code for adventurers with old statuses
                hp_recovery = min(
                    adventurer.hp_max - adventurer.hp_current,  # Can't go above max
                    int(adventurer.hp_max * 0.1 * days_to_advance)  # Legacy: 10% per day
                )
                adventurer.hp_current += hp_recovery
                
                # If above 50% health, make available
                if adventurer.hp_current >= (adventurer.hp_max * 0.5):
                    adventurer.is_available = True
                    adventurer.expedition_status = "available"
    
    db.commit()
    db.refresh(game_time)
    
    # Get updated data for the time panel
    active_expeditions = db.query(Expedition).filter(
        Expedition.result == "in_progress"
    ).all()
    
    unavailable_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == False,
        Adventurer.on_expedition == False
    ).count()
    
    # Get healing adventurers to display
    healing_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == False,
        Adventurer.on_expedition == False,
        Adventurer.expedition_status.in_(["healing", "injured"])
    ).all()
    
    # Return updated time panel HTML
    return templates.TemplateResponse(
        "partials/time_panel.html", 
        {
            "request": request,
            "game_time": game_time,
            "active_expeditions": active_expeditions,
            "unavailable_adventurers": unavailable_adventurers,
            "expeditions_returned": expeditions_returned,
            "healing_adventurers": healing_adventurers
        }
    )

# --- Expedition Endpoints ---
@app.post("/expeditions/", response_model=ExpeditionResult)
def launch_expedition(expedition_data: ExpeditionCreate, db: Session = Depends(get_db)):
    """Launch a new expedition with a party to a dungeon"""
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
    
    # Get the current game day for timing the expedition
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    current_day = game_time.current_day
    duration_days = expedition_data.duration_days if hasattr(expedition_data, 'duration_days') else 7
    return_day = current_day + duration_days
    
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
    party_id = expedition_data.party_id
    simulator_party_idx = None
    for idx, sim_party in enumerate(simulator.parties):
        if len(sim_party) > 0 and sim_party[0].get("id") == party_members[0]["id"]:
            simulator_party_idx = idx
            break
    
    if simulator_party_idx is None:
        simulator_party_idx = simulator.add_party(party_members)
    
    # Start expedition in simulator
    expedition_id = simulator.start_expedition(
        simulator_party_idx, 
        dungeon_level=expedition_data.dungeon_level
    )
    
    # Create expedition record in database
    db_expedition = Expedition(
        party_id=party.id,
        start_day=current_day,
        duration_days=duration_days,
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
    
    # In the time-based system, don't run the expedition immediately
    # Instead, return a placeholder result that tells the UI it's in progress
    result = {
        "expedition_id": db_expedition.id,
        "party_id": party.id,
        "dungeon_level": expedition_data.dungeon_level,
        "turns": 0,  # No turns completed yet
        "start_day": current_day,
        "duration_days": duration_days,
        "return_day": return_day,
        "start_time": db_expedition.started_at,
        "end_time": None,  # Not finished yet
        "treasure_total": 0,  # Unknown until completion
        "special_items": [],
        "xp_earned": 0,  # Unknown until completion
        "xp_per_party_member": 0,  # Unknown until completion
        "resources_used": {"hp_lost": 0, "spells_used": 0, "supplies_used": 0},
        "supplies_consumed": supplies_consumed,
        "equipment_lost": {},  # Unknown until completion
        "dead_members": [],  # Unknown until completion
        "party_status": {
            "members_total": len(party.members),
            "members_alive": len(party.members),
            "members_dead": 0,
            "hp_current": sum(m.hp_current for m in party.members),
            "hp_max": sum(m.hp_max for m in party.members),
            "hp_percentage": (sum(m.hp_current for m in party.members) / 
                             sum(m.hp_max for m in party.members)) * 100 if sum(m.hp_max for m in party.members) > 0 else 0
        },
        "log": []  # Will be populated during expedition
    }
    
    # Return expedition status
    return result

@app.get("/expeditions/{expedition_id}", response_model=ExpeditionResult)
def get_expedition_results(expedition_id: int, db: Session = Depends(get_db)):
    """Get detailed results of an expedition"""
    # First, check if the expedition exists in the database
    db_expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not db_expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    # Get the current game day
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    # Get party data
    party = db.query(Party).filter(Party.id == db_expedition.party_id).first()
    
    # If expedition is still in progress, return a status update
    if db_expedition.result == "in_progress":
        days_elapsed = max(0, min(game_time.current_day - db_expedition.start_day, db_expedition.duration_days))
        progress_percentage = (days_elapsed / db_expedition.duration_days) * 100
        days_remaining = max(0, db_expedition.return_day - game_time.current_day)
        
        # Create a result object for in-progress expedition
        result = {
            "expedition_id": expedition_id,
            "party_id": db_expedition.party_id,
            "dungeon_level": 1,  # Default
            "turns": days_elapsed,  # Use days as turns for display
            "start_day": db_expedition.start_day,
            "duration_days": db_expedition.duration_days,
            "return_day": db_expedition.return_day,
            "start_time": db_expedition.started_at,
            "end_time": None,  # Not finished yet
            "treasure_total": 0,  # Unknown until completion
            "special_items": [],
            "xp_earned": 0,
            "xp_per_party_member": 0,
            "resources_used": {"hp_lost": 0, "spells_used": 0, "supplies_used": 0},
            "supplies_consumed": db_expedition.supplies_consumed or {},
            "equipment_lost": {},
            "dead_members": [],
            "party_status": {
                "members_total": len(party.members) if party else 0,
                "members_alive": len(party.members) if party else 0,
                "members_dead": 0,
                "hp_current": sum(m.hp_current for m in party.members) if party else 0,
                "hp_max": sum(m.hp_max for m in party.members) if party else 0,
                "hp_percentage": (sum(m.hp_current for m in party.members) / 
                                 sum(m.hp_max for m in party.members)) * 100 if party and sum(m.hp_max for m in party.members) > 0 else 0
            },
            "log": [],
            "days_remaining": days_remaining,
            "progress_percentage": progress_percentage,
            "party_members_ready_for_level_up": []
        }
        
        return result
    
    # For completed expeditions, return full results
    try:
        # Try to get results from simulator
        result = simulator.get_expedition_results(expedition_id)
        
        # Add time data to the results
        result["start_day"] = db_expedition.start_day
        result["duration_days"] = db_expedition.duration_days
        result["return_day"] = db_expedition.return_day
        
        # Add level-up eligibility for party members
        if "party_members_ready_for_level_up" not in result:
            # Get party and check for members who can level up
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
            "start_day": db_expedition.start_day,
            "duration_days": db_expedition.duration_days,
            "return_day": db_expedition.return_day,
            "start_time": db_expedition.started_at,
            "end_time": db_expedition.finished_at,
            "treasure_total": sum(node.loot for node in node_results),
            "special_items": [],
            "xp_earned": sum(node.xp_earned for node in node_results),
            "xp_per_party_member": sum(node.xp_earned for node in node_results) / max(1, len(party.members)) if party else 0,
            "resources_used": {"hp_lost": 0, "spells_used": 0, "supplies_used": 0},
            "supplies_consumed": db_expedition.supplies_consumed or {},
            "equipment_lost": db_expedition.equipment_lost or {},
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

# --- Frontend Routes ---
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
    
    # Get current game day
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    # Get active expeditions for time panel
    active_expeditions = db.query(Expedition).filter(
        Expedition.result == "in_progress"
    ).all()
    
    # Check if any adventurers are unavailable due to rest/recovery
    unavailable_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == False,
        Adventurer.on_expedition == False
    ).count()
    
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
    adventurers = db.query(Adventurer).order_by(Adventurer.name).all()
    
    # Add progression data to each adventurer
    adventurers = [add_progression_data(adv) for adv in adventurers]
    
    # Get current game time for healing days remaining
    game_time = db.query(GameTime).first()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "adventurers.html", 
        {
            "request": request, 
            "adventurers": adventurers, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
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

@app.get("/adventurers/filter", response_class=HTMLResponse)
def filter_adventurers(
    request: Request, 
    class_filter: Optional[str] = "", 
    availability_filter: Optional[str] = "",
    expedition_filter: Optional[str] = "",
    view_type: str = "list",
    sort_by: str = "name",
    db: Session = Depends(get_db)
):
    """Filter adventurers by class, availability and expedition status"""
    query = db.query(Adventurer)
    
    if class_filter and class_filter != "":
        query = query.filter(Adventurer.adventurer_class == class_filter)
    
    if availability_filter and availability_filter != "":
        if availability_filter == "available":
            query = query.filter(Adventurer.is_available == True)
        elif availability_filter == "unavailable":
            query = query.filter(Adventurer.is_available == False)
    
    if expedition_filter and expedition_filter != "":
        if expedition_filter == "on_expedition":
            query = query.filter(Adventurer.on_expedition == True)
        elif expedition_filter == "healing":
            query = query.filter(Adventurer.expedition_status == "healing")
        elif expedition_filter == "resting":
            query = query.filter(Adventurer.expedition_status == "resting")
        elif expedition_filter == "injured":
            query = query.filter(Adventurer.expedition_status == "injured")
        elif expedition_filter == "available":
            query = query.filter(Adventurer.expedition_status == "available")
    
    # Apply sorting
    if sort_by == "level":
        query = query.order_by(Adventurer.level.desc())
    elif sort_by == "class":
        query = query.order_by(Adventurer.adventurer_class)
    elif sort_by == "hp":
        # Sort by percentage of hp remaining
        query = query.order_by(Adventurer.hp_current / Adventurer.hp_max)
    elif sort_by == "xp":
        query = query.order_by(Adventurer.xp.desc())
    else:  # Default sort by name
        query = query.order_by(Adventurer.name)
    
    adventurers = query.all()
    
    # Add progression data to each adventurer
    adventurers = [add_progression_data(adv) for adv in adventurers]
    
    # Get current game time for healing days remaining
    game_time = db.query(GameTime).first()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Choose template based on view_type
    template = "partials/adventurer_list.html"
    if view_type == "card":
        template = "partials/adventurer_card_view.html"
    
    return templates.TemplateResponse(
        template, 
        {
            "request": request, 
            "adventurers": adventurers, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/adventurers/search", response_class=HTMLResponse)
def search_adventurers(
    request: Request, 
    search: Optional[str] = "", 
    view_type: str = "list",
    db: Session = Depends(get_db)
):
    """Search adventurers by name"""
    if search:
        adventurers = db.query(Adventurer).filter(Adventurer.name.ilike(f"%{search}%")).all()
    else:
        adventurers = db.query(Adventurer).all()
    
    # Add progression data to each adventurer
    adventurers = [add_progression_data(adv) for adv in adventurers]
    
    # Get current game time for healing days remaining
    game_time = db.query(GameTime).first()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Choose template based on view_type
    template = "partials/adventurer_list.html"
    if view_type == "card":
        template = "partials/adventurer_card_view.html"
        
    return templates.TemplateResponse(
        template, 
        {
            "request": request, 
            "adventurers": adventurers, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/adventurers/view", response_class=HTMLResponse)
def toggle_adventurer_view(
    request: Request,
    type: str = "list",
    class_filter: Optional[str] = "",
    availability_filter: Optional[str] = "",
    expedition_filter: Optional[str] = "", 
    search: Optional[str] = "",
    sort_by: str = "name",
    db: Session = Depends(get_db)
):
    """Toggle between list and card views for adventurers"""
    # Build query with all the filters
    query = db.query(Adventurer)
    
    if class_filter and class_filter != "":
        query = query.filter(Adventurer.adventurer_class == class_filter)
    
    if availability_filter and availability_filter != "":
        if availability_filter == "available":
            query = query.filter(Adventurer.is_available == True)
        elif availability_filter == "unavailable":
            query = query.filter(Adventurer.is_available == False)
    
    if expedition_filter and expedition_filter != "":
        if expedition_filter == "on_expedition":
            query = query.filter(Adventurer.on_expedition == True)
        elif expedition_filter == "healing":
            query = query.filter(Adventurer.expedition_status == "healing")
        elif expedition_filter == "resting":
            query = query.filter(Adventurer.expedition_status == "resting")
        elif expedition_filter == "injured":
            query = query.filter(Adventurer.expedition_status == "injured")
        elif expedition_filter == "available":
            query = query.filter(Adventurer.expedition_status == "available")
    
    if search and search != "":
        query = query.filter(Adventurer.name.ilike(f"%{search}%"))
    
    # Apply sorting
    if sort_by == "level":
        query = query.order_by(Adventurer.level.desc())
    elif sort_by == "class":
        query = query.order_by(Adventurer.adventurer_class)
    elif sort_by == "hp":
        # Sort by percentage of hp remaining
        query = query.order_by(Adventurer.hp_current / Adventurer.hp_max)
    elif sort_by == "xp":
        query = query.order_by(Adventurer.xp.desc())
    else:  # Default sort by name
        query = query.order_by(Adventurer.name)
    
    adventurers = query.all()
    
    # Add progression data to each adventurer
    adventurers = [add_progression_data(adv) for adv in adventurers]
    
    # Get current game time for healing days remaining
    game_time = db.query(GameTime).first()
    
    # Get treasury total
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Select template based on view type
    template = "partials/adventurer_list.html"
    if type == "card":
        template = "partials/adventurer_card_view.html"
    
    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "adventurers": adventurers,
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/adventurers/sort", response_class=HTMLResponse)
def sort_adventurers(
    request: Request,
    sort_by: str = "name",
    view_type: str = "list",
    class_filter: Optional[str] = "",
    availability_filter: Optional[str] = "",
    expedition_filter: Optional[str] = "",
    search: Optional[str] = "",
    db: Session = Depends(get_db)
):
    """Sort adventurers by different criteria"""
    # Build query with all the filters
    query = db.query(Adventurer)
    
    if class_filter and class_filter != "":
        query = query.filter(Adventurer.adventurer_class == class_filter)
    
    if availability_filter and availability_filter != "":
        if availability_filter == "available":
            query = query.filter(Adventurer.is_available == True)
        elif availability_filter == "unavailable":
            query = query.filter(Adventurer.is_available == False)
    
    if expedition_filter and expedition_filter != "":
        if expedition_filter == "on_expedition":
            query = query.filter(Adventurer.on_expedition == True)
        elif expedition_filter == "healing":
            query = query.filter(Adventurer.expedition_status == "healing")
        elif expedition_filter == "resting":
            query = query.filter(Adventurer.expedition_status == "resting")
        elif expedition_filter == "injured":
            query = query.filter(Adventurer.expedition_status == "injured")
        elif expedition_filter == "available":
            query = query.filter(Adventurer.expedition_status == "available")
    
    if search and search != "":
        query = query.filter(Adventurer.name.ilike(f"%{search}%"))
    
    # Apply sorting
    if sort_by == "level":
        query = query.order_by(Adventurer.level.desc())
    elif sort_by == "class":
        query = query.order_by(Adventurer.adventurer_class)
    elif sort_by == "hp":
        # Sort by percentage of hp remaining
        query = query.order_by(Adventurer.hp_current / Adventurer.hp_max)
    elif sort_by == "xp":
        query = query.order_by(Adventurer.xp.desc())
    else:  # Default sort by name
        query = query.order_by(Adventurer.name)
    
    adventurers = query.all()
    
    # Add progression data to each adventurer
    adventurers = [add_progression_data(adv) for adv in adventurers]
    
    # Get current game time for healing days remaining
    game_time = db.query(GameTime).first()
    
    # Get treasury total
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Select template based on view type
    template = "partials/adventurer_list.html"
    if view_type == "card":
        template = "partials/adventurer_card_view.html"
    
    return templates.TemplateResponse(
        template,
        {
            "request": request,
            "adventurers": adventurers,
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/adventurers/{adventurer_id}", response_class=HTMLResponse)
def get_adventurer_details(request: Request, adventurer_id: int, db: Session = Depends(get_db)):
    """Get details of a specific adventurer"""
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    
    # Add progression data
    adventurer = add_progression_data(adventurer)
    
    # Get current game time for healing days remaining
    game_time = db.query(GameTime).first()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
        
    return templates.TemplateResponse(
        "partials/adventurer_details.html", 
        {
            "request": request, 
            "adventurer": adventurer, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
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
    
    return templates.TemplateResponse(
        "parties.html", 
        {"request": request, "parties": parties, "treasury_gold": treasury_gold}
    )

@app.get("/parties/create-form", response_class=HTMLResponse)
def party_create_form(request: Request, db: Session = Depends(get_db)):
    """Return the party creation form"""
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "partials/party_form.html", 
        {"request": request, "treasury_gold": treasury_gold}
    )

@app.get("/parties/{party_id}/add-member-form", response_class=HTMLResponse)
def add_party_member_form(request: Request, party_id: int, db: Session = Depends(get_db)):
    """Return the form to add a member to a party"""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
        
    # Get adventurers that are available and not already in this party
    available_adventurers = db.query(Adventurer).filter(
        Adventurer.is_available == True,
        ~Adventurer.parties.any(Party.id == party_id)
    ).all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "partials/add_party_member.html", 
        {"request": request, "party": party, "available_adventurers": available_adventurers, "treasury_gold": treasury_gold}
    )

@app.get("/expeditions", response_class=HTMLResponse)
def expeditions_page(request: Request, db: Session = Depends(get_db)):
    """Render the expeditions page"""
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Get current game day
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    return templates.TemplateResponse(
        "expeditions.html", 
        {
            "request": request, 
            "active_expeditions": active_expeditions, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/expeditions/active", response_class=HTMLResponse)
def active_expeditions(request: Request, db: Session = Depends(get_db)):
    """Return active expeditions for the expeditions page"""
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    
    # Get parties on expedition
    parties_on_expedition = db.query(Party).filter(Party.on_expedition == True).all()
    expedition_parties = {}
    
    for party in parties_on_expedition:
        if party.current_expedition_id:
            expedition_parties[party.current_expedition_id] = party
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    # Get current game day
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime()
        db.add(game_time)
        db.commit()
        db.refresh(game_time)
    
    return templates.TemplateResponse(
        "partials/active_expeditions.html", 
        {
            "request": request, 
            "active_expeditions": active_expeditions, 
            "expedition_parties": expedition_parties, 
            "treasury_gold": treasury_gold,
            "game_time": game_time
        }
    )

@app.get("/expeditions/completed", response_class=HTMLResponse)
def completed_expeditions(request: Request, db: Session = Depends(get_db)):
    """Return completed expeditions for the expeditions page"""
    completed_expeditions = db.query(Expedition).filter(Expedition.result == "completed").order_by(Expedition.finished_at.desc()).all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "partials/completed_expeditions.html", 
        {"request": request, "completed_expeditions": completed_expeditions, "treasury_gold": treasury_gold}
    )

@app.get("/expeditions/create-form", response_class=HTMLResponse)
def expedition_create_form(request: Request, party_id: int = None, db: Session = Depends(get_db)):
    """Return the expedition creation form"""
    party = None
    parties = []
    
    if party_id:
        party = db.query(Party).filter(Party.id == party_id).first()
        if not party:
            raise HTTPException(status_code=404, detail="Party not found")
    else:
        parties = db.query(Party).all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "partials/expedition_form.html", 
        {"request": request, "party": party, "parties": parties, "treasury_gold": treasury_gold}
    )

@app.get("/players", response_class=HTMLResponse)
def players_page(request: Request, db: Session = Depends(get_db)):
    """Render the players page"""
    players = db.query(Player).all()
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "players.html", 
        {"request": request, "players": players, "treasury_gold": treasury_gold}
    )

@app.get("/players/create-form", response_class=HTMLResponse)
def player_create_form(request: Request, db: Session = Depends(get_db)):
    """Return the player creation form"""
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "partials/player_form.html", 
        {"request": request, "treasury_gold": treasury_gold}
    )

@app.get("/expeditions/{expedition_id}", response_class=HTMLResponse)
def expedition_details(request: Request, expedition_id: int, db: Session = Depends(get_db)):
    """Show details of a specific expedition"""
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    try:
        # Get the detailed results from the simulator
        expedition_results = simulator.get_expedition_results(expedition_id)
    except ValueError:
        # If not in simulator, create a dummy result
        expedition_results = {
            "expedition_id": expedition_id,
            "party_id": expedition.party_id,
            "dungeon_level": 1,
            "turns": len(expedition.node_results),
            "start_time": expedition.started_at,
            "end_time": expedition.finished_at,
            "treasure_total": sum(node.loot for node in expedition.node_results),
            "special_items": [],
            "xp_earned": sum(node.xp_earned for node in expedition.node_results),
            "xp_per_party_member": sum(node.xp_earned for node in expedition.node_results) / max(1, len(expedition.party.members)),
            "resources_used": {"hp_lost": 0, "spells_used": 0, "supplies_used": 0},
            "dead_members": [log.adventurer.name for log in expedition.party.expedition_logs if log.status == "dead"],
            "party_status": {
                "members_total": len(expedition.party.members),
                "members_alive": len([m for m in expedition.party.members if m.hp_current > 0]),
                "members_dead": len([log for log in expedition.party.expedition_logs if log.status == "dead"]),
                "hp_current": sum(m.hp_current for m in expedition.party.members),
                "hp_max": sum(m.hp_max for m in expedition.party.members),
                "hp_percentage": (sum(m.hp_current for m in expedition.party.members) / 
                                 sum(m.hp_max for m in expedition.party.members)) * 100
            },
            "log": []
        }
    
    # Get treasury total from the first player for header display
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury
    
    return templates.TemplateResponse(
        "expedition_result.html", 
        {"request": request, "expedition": expedition, "expedition_results": expedition_results, "treasury_gold": treasury_gold}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # for local testing
