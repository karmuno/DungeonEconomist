from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
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
    title="Dungeon Economist",
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
    
    # Check if party is already on an expedition
    if party.on_expedition:
        raise HTTPException(status_code=400, detail="Party is already on an expedition")
    
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
    
    # Update party status to on expedition
    party.on_expedition = True
    party.current_expedition_id = db_expedition.id
    
    # Update all adventurers in the party
    for member in party.members:
        member.on_expedition = True
        member.expedition_status = "active"
        member.is_available = False
    
    db.commit()
    
    # Run expedition to completion
    result = simulator.run_expedition_to_completion(expedition_id)
    
    # Update expedition in database
    db_expedition.finished_at = datetime.now()
    db_expedition.result = "completed"
    
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
            
    db.commit()
    
    # Return full expedition results
    return result

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
        
        # Create a result object
        result = {
            "expedition_id": expedition_id,
            "party_id": db_expedition.party_id,
            "dungeon_level": 1,  # Default
            "turns": len(node_results),
            "start_time": db_expedition.started_at,
            "end_time": db_expedition.finished_at,
            "treasure_total": sum(node.loot for node in node_results),
            "special_items": [],
            "xp_earned": sum(node.xp_earned for node in node_results),
            "xp_per_party_member": sum(node.xp_earned for node in node_results) / max(1, len(party.members)) if party else 0,
            "resources_used": {"hp_lost": 0, "spells_used": 0, "supplies_used": 0},
            "dead_members": [log.adventurer.name for log in expedition_logs if log.status == "dead"],
            "party_status": party_status,
            "log": log
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
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "adventurer_count": adventurer_count,
            "party_count": party_count,
            "expedition_count": expedition_count,
            "recent_expeditions": recent_expeditions
        }
    )

@app.get("/adventurers", response_class=HTMLResponse)
def adventurers_page(request: Request, db: Session = Depends(get_db)):
    """Render the adventurers page"""
    adventurers = db.query(Adventurer).all()
    return templates.TemplateResponse(
        "adventurers.html", 
        {"request": request, "adventurers": adventurers}
    )

@app.get("/adventurers/create-form", response_class=HTMLResponse)
def adventurer_create_form(request: Request):
    """Return the adventurer creation form"""
    return templates.TemplateResponse(
        "partials/adventurer_form.html", 
        {"request": request}
    )

@app.get("/adventurers/filter", response_class=HTMLResponse)
def filter_adventurers(
    request: Request, 
    class_filter: str = None, 
    availability_filter: str = None,
    expedition_filter: str = None,
    db: Session = Depends(get_db)
):
    """Filter adventurers by class, availability and expedition status"""
    query = db.query(Adventurer)
    
    if class_filter:
        query = query.filter(Adventurer.adventurer_class == class_filter)
    
    if availability_filter == "available":
        query = query.filter(Adventurer.is_available == True)
    elif availability_filter == "unavailable":
        query = query.filter(Adventurer.is_available == False)
    
    if expedition_filter:
        if expedition_filter == "on_expedition":
            query = query.filter(Adventurer.on_expedition == True)
        elif expedition_filter == "resting":
            query = query.filter(Adventurer.expedition_status == "resting")
        elif expedition_filter == "injured":
            query = query.filter(Adventurer.expedition_status == "injured")
        elif expedition_filter == "active":
            query = query.filter(Adventurer.expedition_status == "active")
    
    adventurers = query.all()
    
    return templates.TemplateResponse(
        "partials/adventurer_list.html", 
        {"request": request, "adventurers": adventurers}
    )

@app.get("/adventurers/search", response_class=HTMLResponse)
def search_adventurers(request: Request, search: str = "", db: Session = Depends(get_db)):
    """Search adventurers by name"""
    if search:
        adventurers = db.query(Adventurer).filter(Adventurer.name.ilike(f"%{search}%")).all()
    else:
        adventurers = db.query(Adventurer).all()
        
    return templates.TemplateResponse(
        "partials/adventurer_list.html", 
        {"request": request, "adventurers": adventurers}
    )

@app.get("/adventurers/{adventurer_id}", response_class=HTMLResponse)
def get_adventurer_details(request: Request, adventurer_id: int, db: Session = Depends(get_db)):
    """Get details of a specific adventurer"""
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
        
    return templates.TemplateResponse(
        "partials/adventurer_details.html", 
        {"request": request, "adventurer": adventurer}
    )

@app.get("/parties", response_class=HTMLResponse)
def parties_page(request: Request, db: Session = Depends(get_db)):
    """Render the parties page"""
    parties = db.query(Party).all()
    return templates.TemplateResponse(
        "parties.html", 
        {"request": request, "parties": parties}
    )

@app.get("/parties/create-form", response_class=HTMLResponse)
def party_create_form(request: Request):
    """Return the party creation form"""
    return templates.TemplateResponse(
        "partials/party_form.html", 
        {"request": request}
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
    
    return templates.TemplateResponse(
        "partials/add_party_member.html", 
        {"request": request, "party": party, "available_adventurers": available_adventurers}
    )

@app.get("/expeditions", response_class=HTMLResponse)
def expeditions_page(request: Request, db: Session = Depends(get_db)):
    """Render the expeditions page"""
    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    
    return templates.TemplateResponse(
        "expeditions.html", 
        {"request": request, "active_expeditions": active_expeditions}
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
    
    return templates.TemplateResponse(
        "partials/active_expeditions.html", 
        {"request": request, "active_expeditions": active_expeditions, "expedition_parties": expedition_parties}
    )

@app.get("/expeditions/completed", response_class=HTMLResponse)
def completed_expeditions(request: Request, db: Session = Depends(get_db)):
    """Return completed expeditions for the expeditions page"""
    completed_expeditions = db.query(Expedition).filter(Expedition.result == "completed").order_by(Expedition.finished_at.desc()).all()
    
    return templates.TemplateResponse(
        "partials/completed_expeditions.html", 
        {"request": request, "completed_expeditions": completed_expeditions}
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
    
    return templates.TemplateResponse(
        "partials/expedition_form.html", 
        {"request": request, "party": party, "parties": parties}
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
    
    return templates.TemplateResponse(
        "expedition_result.html", 
        {"request": request, "expedition": expedition, "expedition_results": expedition_results}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # for local testing
