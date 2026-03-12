from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.database import create_tables, get_db
from app.models import Adventurer, Party, Expedition, Player, GameTime
from app.routes import adventurers, players, parties, equipment, expeditions, game

# Create tables on startup
create_tables()

# FastAPI app
app = FastAPI(
    title="Venturekeep",
    description="D&D Party Management Simulation",
    version="0.1.0"
)

# CORS (permissive for local dev)
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

# Register route modules
app.include_router(adventurers.router)
app.include_router(players.router)
app.include_router(parties.router)
app.include_router(equipment.router)
app.include_router(expeditions.router)
app.include_router(game.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    """Render the home page"""
    adventurer_count = db.query(Adventurer).count()
    party_count = db.query(Party).count()
    expedition_count = db.query(Expedition).count()

    recent_expeditions = db.query(Expedition).order_by(Expedition.started_at.desc()).limit(5).all()

    player = db.query(Player).first()
    if not player:
        player = Player(name="Default Player", treasury=0, total_score=0)
        db.add(player)
        db.commit()
        db.refresh(player)

    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)

    active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
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


@app.get("/players", response_class=HTMLResponse)
def players_page(request: Request, db: Session = Depends(get_db)):
    """Render the players page"""
    all_players = db.query(Player).all()

    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury

    return templates.TemplateResponse(
        "players.html",
        {"request": request, "players": all_players, "treasury_gold": treasury_gold}
    )
