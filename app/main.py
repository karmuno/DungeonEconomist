from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json

from app.models import Base, Adventurer, Party, DungeonNode, Expedition, ExpeditionNodeResult, ExpeditionLog
from app.schemas import (
    AdventurerOut, AdventurerCreate, PartyCreate, 
    PartyOut, PartyMemberOperation, ExpeditionCreate,
    ExpeditionResult, TurnResult
)
from app.simulator import DungeonSimulator

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
    title="D&D Party Sim API",
    description="Backend for managing adventurers, parties, and dungeon expeditions",
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

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        is_available=True
    )
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return adv

@app.get("/adventurers/", response_model=list[AdventurerOut])
def list_adventurers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Adventurer).offset(skip).limit(limit).all()

# --- Party Endpoints ---
@app.post("/parties/", response_model=PartyOut)
def create_party(party: PartyCreate, db: Session = Depends(get_db)):
    new_party = Party(name=party.name, created_at=datetime.now())
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

@app.post("/parties/add-member/", response_model=PartyOut)
def add_adventurer_to_party(operation: PartyMemberOperation, db: Session = Depends(get_db)):
    # Check if party exists
    party = db.query(Party).filter(Party.id == operation.party_id).first()
    if party is None:
        raise HTTPException(status_code=404, detail="Party not found")
    
    # Check if adventurer exists and is available
    adventurer = db.query(Adventurer).filter(
        Adventurer.id == operation.adventurer_id,
        Adventurer.is_available == True
    ).first()
    if adventurer is None:
        raise HTTPException(
            status_code=404, 
            detail="Adventurer not found or already assigned to an expedition"
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

# Create shared simulator instance
simulator = DungeonSimulator()

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
    
    # Convert party to format needed for simulator
    party_members = []
    for member in party.members:
        party_members.append({
            "id": member.id,
            "name": member.name,
            "character_class": member.adventurer_class.value,
            "level": member.level,
            "hit_points": member.hp_max,
            "current_hp": member.hp_current,
            "xp": member.xp,
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
        started_at=datetime.now(),
        result="in_progress"
    )
    db.add(db_expedition)
    db.commit()
    db.refresh(db_expedition)
    
    # Run expedition to completion
    result = simulator.run_expedition_to_completion(expedition_id)
    
    # Update expedition in database
    db_expedition.finished_at = datetime.now()
    db_expedition.result = "completed"
    
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
        else:
            member.hp_current = max(1, member.hp_current - 5)  # Some HP loss
            
    db.commit()
    
    # Return full expedition results
    return result

@app.get("/expeditions/{expedition_id}", response_model=ExpeditionResult)
def get_expedition_results(expedition_id: int):
    """Get detailed results of an expedition"""
    try:
        result = simulator.get_expedition_results(expedition_id)
        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Expedition not found")

@app.get("/expeditions/", response_model=list)
def list_expeditions(db: Session = Depends(get_db)):
    """List all expeditions in the database"""
    return db.query(Expedition).all()

@app.post("/expeditions/{expedition_id}/advance", response_model=TurnResult)
def advance_expedition_turn(expedition_id: int):
    """Advance an expedition by one turn"""
    try:
        result = simulator.advance_turn(expedition_id)
        return result
    except ValueError:
        raise HTTPException(status_code=404, detail="Expedition not found or already completed")

# Root
@app.get("/")
def read_root():
    return {"message": "Welcome to D&D Party Sim API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # for local testing
