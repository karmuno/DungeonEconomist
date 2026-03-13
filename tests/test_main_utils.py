import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import math
from datetime import datetime, timedelta

from app.main import app
from app.database import get_db
from app.models import Base, Adventurer, AdventurerClass, GameTime, Party, Expedition, Player
from app.schemas import AdventurerCreate, PartyCreate, GameTimeInfo

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override for tests
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    return TestClient(app)

# Helper to create adventurer
def create_adventurer_db(db: Session, name: str, xp: int, gold: int, is_bankrupt: bool = False):
    adv = Adventurer(
        name=name,
        adventurer_class=AdventurerClass.FIGHTER,
        level=1,
        xp=xp,
        gold=gold,
        hp_max=10,
        hp_current=10,
        is_available=True,
        is_bankrupt=is_bankrupt,
    )
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return adv

# Helper to create GameTime
def create_game_time_db(db: Session, current_day: int):
    gt = GameTime(current_day=current_day)
    db.add(gt)
    db.commit()
    db.refresh(gt)
    return gt

# Helper to create Player
def create_player_db(db: Session, name: str, treasury_gold: int = 0, total_score: int = 0):
    player = Player(name=name, treasury_gold=treasury_gold, treasury_silver=0, treasury_copper=0, total_score=total_score)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player

# Test Cases

def test_upkeep_successful_payment(client: TestClient, db_session: Session):
    player = create_player_db(db_session, name="TestPlayer1")
    create_game_time_db(db_session, 29)  # advance_day will move to 30
    adv_xp = 2000
    adv_gold_initial = 100
    # Upkeep cost: 1 copper per XP = 2000cp = 20gp
    upkeep_cost_copper = math.floor(adv_xp * 1)
    adv = create_adventurer_db(db_session, name="TestAdv1", xp=adv_xp, gold=adv_gold_initial)

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    db_session.refresh(adv)
    # 100gp = 10000cp, minus 2000cp = 8000cp = 80gp
    assert adv.total_copper() == (adv_gold_initial * 100) - upkeep_cost_copper
    assert not adv.is_bankrupt

    db_session.refresh(player)
    assert player.treasury_total_copper() == upkeep_cost_copper
    assert player.total_score == upkeep_cost_copper

def test_upkeep_adventurer_goes_bankrupt_permanently(client: TestClient, db_session: Session):
    player = create_player_db(db_session, name="TestPlayer2")
    create_game_time_db(db_session, 29)  # advance_day will move to 30
    adv_xp = 2000
    adv_initial_gold = 10  # 10gp = 1000cp, cost = 2000cp -> bankrupt
    adv = create_adventurer_db(db_session, name="TestAdv2", xp=adv_xp, gold=adv_initial_gold)

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.total_copper() == 0
    assert adv.is_bankrupt
    assert adv.bankruptcy_day == 30
    assert not adv.is_available

    db_session.refresh(player)
    assert player.treasury_total_copper() == adv_initial_gold * 100

def test_upkeep_no_upkeep_due_not_day_30(client: TestClient, db_session: Session):
    player = create_player_db(db_session, name="TestPlayer5")
    create_game_time_db(db_session, 28)  # advance_day will move to 29
    adv = create_adventurer_db(db_session, name="TestAdv5", xp=1000, gold=100)

    initial_adv_gold = adv.gold

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == initial_adv_gold

def test_upkeep_zero_xp_adventurer(client: TestClient, db_session: Session):
    player = create_player_db(db_session, name="TestPlayer6")
    create_game_time_db(db_session, 29)  # advance_day will move to 30
    adv = create_adventurer_db(db_session, name="TestAdv6", xp=0, gold=0)

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 0
    assert not adv.is_bankrupt

def test_bankrupt_adventurer_cannot_launch_expedition(client: TestClient, db_session: Session):
    party = Party(name="Bankrupt Party")
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    adv_bankrupt = create_adventurer_db(db_session, name="BankruptAdv", xp=100, gold=0, is_bankrupt=True)
    party.members.append(adv_bankrupt)
    db_session.commit()

    expedition_data = {
        "party_id": party.id,
        "dungeon_level": 1,
        "duration_days": 5
    }
    response = client.post("/expeditions/", json=expedition_data)

    assert response.status_code == 400
    assert "bankrupt" in response.json()["detail"].lower()

def test_non_bankrupt_party_launches_expedition(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 1)

    party = Party(name="Solvent Party")
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    adv_solvent = create_adventurer_db(db_session, name="SolventAdv", xp=100, gold=100, is_bankrupt=False)
    party.members.append(adv_solvent)
    db_session.commit()

    expedition_data = {
        "party_id": party.id,
        "dungeon_level": 1,
        "duration_days": 5
    }
    response = client.post("/expeditions/", json=expedition_data)

    assert response.status_code == 200
    assert "expedition_id" in response.json()


# --- Tests for /time/advance-day ---

def test_advance_day_existing_gametime(client: TestClient, db_session: Session):
    initial_datetime = datetime.now() - timedelta(hours=1)
    gt = GameTime(current_day=5, day_started_at=initial_datetime, last_updated=initial_datetime)
    db_session.add(gt)
    db_session.commit()

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    data = response.json()
    assert data["current_day"] == 6

def test_advance_day_no_initial_gametime_returns_404(client: TestClient, db_session: Session):
    assert db_session.query(GameTime).first() is None

    response = client.post("/time/advance-day")
    assert response.status_code == 404

def test_advance_day_heals_adventurers(client: TestClient, db_session: Session):
    """Adventurers heal 1 HP per day when not on expedition"""
    create_game_time_db(db_session, 10)
    adv = Adventurer(
        name="Wounded",
        adventurer_class=AdventurerClass.FIGHTER,
        level=1, xp=0, gold=0,
        hp_max=10, hp_current=5,
        is_available=False,
    )
    db_session.add(adv)
    db_session.commit()
    db_session.refresh(adv)

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.hp_current == 6
    assert not adv.is_available  # Still not full HP

def test_advance_day_adventurer_becomes_available_at_full_hp(client: TestClient, db_session: Session):
    """Adventurer becomes available when healed to full HP"""
    create_game_time_db(db_session, 10)
    adv = Adventurer(
        name="AlmostHealed",
        adventurer_class=AdventurerClass.FIGHTER,
        level=1, xp=0, gold=0,
        hp_max=10, hp_current=9,
        is_available=False,
    )
    db_session.add(adv)
    db_session.commit()
    db_session.refresh(adv)

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.hp_current == 10
    assert adv.is_available

def test_game_time_returns_404_when_no_game(client: TestClient, db_session: Session):
    """GET /time/ should return 404 when no game exists"""
    assert db_session.query(GameTime).first() is None

    response = client.get("/time/")
    assert response.status_code == 404


def test_new_game_creates_adventurers_and_starts_at_day_1(client: TestClient, db_session: Session):
    """POST /game/new should create 6 adventurers and start at day 1"""
    assert db_session.query(Adventurer).count() == 0

    response = client.post("/game/new", json={"keep_name": "Test Keep"})
    assert response.status_code == 200

    data = response.json()
    assert data["current_day"] == 1
    assert data["keep_name"] == "Test Keep"

    # Should have 6 adventurers (one per class)
    assert db_session.query(Adventurer).count() == 6

    # Should have one player named "Test Keep"
    player = db_session.query(Player).first()
    assert player is not None
    assert player.name == "Test Keep"


# --- Test for POST /parties/ ---
def test_create_party_successful_response(client: TestClient, db_session: Session):
    party_name = "The Mighty Testers"

    response = client.post("/parties/", json={"name": party_name})
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == party_name
    assert data["on_expedition"] is False
    assert data["members"] == []
    assert isinstance(data["id"], int)
    assert data["id"] > 0
