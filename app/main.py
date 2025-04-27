from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

from app.models import Base, Adventurer, Party, DungeonNode, Expedition
from app.schemas import (
    AdventurerOut, AdventurerCreate, PartyCreate, 
    PartyOut, PartyMemberOperation
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

# --- Expedition Endpoints (skeleton) ---
@app.post("/expeditions/", response_model=None)
def launch_expedition(party_id: int, db: Session = Depends(get_db)):
    # TODO: implement expedition logic in simulator
    party = db.query(Party).get(party_id)
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    expedition = Expedition(party_id=party_id)
    db.add(expedition)
    db.commit()
    db.refresh(expedition)
    return expedition

@app.get("/expeditions/", response_model=list)
def list_expeditions(db: Session = Depends(get_db)):
    return db.query(Expedition).all()

# Root
@app.get("/")
def read_root():
    return {"message": "Welcome to D&D Party Sim API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # for local testing
