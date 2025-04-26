from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base, Adventurer, Party, DungeonNode, Expedition
from app.schemas import AdventurerOut

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
@app.post("/adventurers/", response_model=None)
def create_adventurer(name: str, adventurer_class: str, db: Session = Depends(get_db)):
    # TODO: validate class enum
    adv = Adventurer(name=name, adventurer_class=adventurer_class)
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return adv

@app.get("/adventurers/", response_model=list[AdventurerOut])
def list_adventurers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Adventurer).offset(skip).limit(limit).all()

# --- Party Endpoints ---
@app.post("/parties/", response_model=None)
def create_party(name: str = "New Party", db: Session = Depends(get_db)):
    party = Party(name=name)
    db.add(party)
    db.commit()
    db.refresh(party)
    return party

@app.get("/parties/", response_model=list)
def list_parties(db: Session = Depends(get_db)):
    return db.query(Party).all()

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
