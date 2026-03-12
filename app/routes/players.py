from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Player
from app.schemas import PlayerCreate, PlayerOut, PlayerBase, PartyOut

router = APIRouter()


@router.post("/players/", response_model=PlayerOut)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player"""
    db_player = Player(name=player.name, treasury=0, total_score=0)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player


@router.get("/players/", response_model=List[PlayerOut])
def list_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all players"""
    return db.query(Player).offset(skip).limit(limit).all()


@router.get("/players/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    """Get a specific player by ID"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.put("/players/{player_id}", response_model=PlayerOut)
def update_player(player_id: int, player_data: PlayerBase, db: Session = Depends(get_db)):
    """Update a player's information"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    player.name = player_data.name
    db.commit()
    db.refresh(player)
    return player


@router.get("/players/{player_id}/parties", response_model=List[PartyOut])
def get_player_parties(player_id: int, db: Session = Depends(get_db)):
    """Get all parties belonging to a player"""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player.parties
