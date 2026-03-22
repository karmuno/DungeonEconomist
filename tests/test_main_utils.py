import math
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models import Account, Adventurer, AdventurerClass, Base, Keep, Party

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


def create_account_and_keep(db: Session, username: str = "testuser", keep_name: str = "Test Keep") -> tuple[Account, Keep, str]:
    """Create an account and keep, return (account, keep, token)."""
    account = Account(
        username=username,
        password_hash=hash_password("testpass1"),
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    now = datetime.now()
    keep = Keep(
        account_id=account.id,
        name=keep_name,
        treasury_gold=0,
        treasury_silver=0,
        treasury_copper=0,
        total_score=0,
        current_day=1,
        day_started_at=now,
        last_updated=now,
        created_at=now,
    )
    db.add(keep)
    db.commit()
    db.refresh(keep)

    token = create_access_token(account.id)
    return account, keep, token


def auth_headers(token: str, keep_id: int) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "X-Keep-Id": str(keep_id),
    }


@pytest.fixture(scope="function")
def client(db_session):
    return TestClient(app)

# Helper to create adventurer
def create_adventurer_db(db: Session, keep_id: int, name: str, xp: int, gold: int, is_bankrupt: bool = False):
    adv = Adventurer(
        keep_id=keep_id,
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

# Test Cases

def test_upkeep_successful_payment(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 29  # advance_day will move to 30
    db_session.commit()

    adv_xp = 2000
    adv_gold_initial = 100
    upkeep_cost_copper = math.floor(adv_xp * 1)
    adv = create_adventurer_db(db_session, keep.id, name="TestAdv1", xp=adv_xp, gold=adv_gold_initial)

    response = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.total_copper() == (adv_gold_initial * 100) - upkeep_cost_copper
    assert not adv.is_bankrupt

    db_session.refresh(keep)
    assert keep.treasury_total_copper() == upkeep_cost_copper
    assert keep.total_score == upkeep_cost_copper

def test_upkeep_adventurer_goes_bankrupt_permanently(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 29  # advance_day will move to 30
    db_session.commit()

    adv_xp = 2000
    adv_initial_gold = 10  # 10gp = 1000cp, cost = 2000cp -> bankrupt
    adv = create_adventurer_db(db_session, keep.id, name="TestAdv2", xp=adv_xp, gold=adv_initial_gold)

    response = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.total_copper() == 0
    assert adv.is_bankrupt
    assert adv.bankruptcy_day == 30
    assert not adv.is_available

    db_session.refresh(keep)
    assert keep.treasury_total_copper() == adv_initial_gold * 100

def test_upkeep_no_upkeep_due_not_day_30(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 28  # advance_day will move to 29
    db_session.commit()

    adv = create_adventurer_db(db_session, keep.id, name="TestAdv5", xp=1000, gold=100)
    initial_adv_gold = adv.gold

    response = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == initial_adv_gold

def test_upkeep_zero_xp_adventurer(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 29  # advance_day will move to 30
    db_session.commit()

    adv = create_adventurer_db(db_session, keep.id, name="TestAdv6", xp=0, gold=0)

    response = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 0
    assert not adv.is_bankrupt

def test_bankrupt_adventurer_cannot_launch_expedition(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)

    party = Party(name="Bankrupt Party", keep_id=keep.id)
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    adv_bankrupt = create_adventurer_db(db_session, keep.id, name="BankruptAdv", xp=100, gold=0, is_bankrupt=True)
    party.members.append(adv_bankrupt)
    db_session.commit()

    expedition_data = {
        "party_id": party.id,
        "dungeon_level": 1
    }
    response = client.post("/expeditions/", json=expedition_data, headers=auth_headers(token, keep.id))

    assert response.status_code == 400
    assert "bankrupt" in response.json()["detail"].lower()

def test_non_bankrupt_party_launches_expedition(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)

    party = Party(name="Solvent Party", keep_id=keep.id)
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    adv_solvent = create_adventurer_db(db_session, keep.id, name="SolventAdv", xp=100, gold=100, is_bankrupt=False)
    party.members.append(adv_solvent)
    db_session.commit()

    expedition_data = {
        "party_id": party.id,
        "dungeon_level": 1
    }
    response = client.post("/expeditions/", json=expedition_data, headers=auth_headers(token, keep.id))

    assert response.status_code == 200
    assert "expedition_id" in response.json()


# --- Tests for /time/advance-day ---

def test_advance_day_existing_gametime(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 5
    db_session.commit()

    response = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert response.status_code == 200

    data = response.json()
    assert data["current_day"] == 6

def test_advance_day_no_auth_returns_401(client: TestClient, db_session: Session):
    response = client.post("/time/advance-day")
    assert response.status_code in (401, 403)

def test_advance_day_heals_adventurers(client: TestClient, db_session: Session):
    """Adventurers heal 1 HP per day when not on expedition"""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 10
    db_session.commit()

    adv = Adventurer(
        keep_id=keep.id,
        name="Wounded",
        adventurer_class=AdventurerClass.FIGHTER,
        level=1, xp=0, gold=0,
        hp_max=10, hp_current=5,
        is_available=False,
    )
    db_session.add(adv)
    db_session.commit()
    db_session.refresh(adv)

    response = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.hp_current == 6
    assert not adv.is_available  # Still not full HP

def test_advance_day_adventurer_becomes_available_at_full_hp(client: TestClient, db_session: Session):
    """Adventurer becomes available when healed to full HP"""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 10
    db_session.commit()

    adv = Adventurer(
        keep_id=keep.id,
        name="AlmostHealed",
        adventurer_class=AdventurerClass.FIGHTER,
        level=1, xp=0, gold=0,
        hp_max=10, hp_current=9,
        is_available=False,
    )
    db_session.add(adv)
    db_session.commit()
    db_session.refresh(adv)

    response = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.hp_current == 10
    assert adv.is_available

def test_game_time_returns_keep_time(client: TestClient, db_session: Session):
    """GET /time/ should return keep time info"""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 42
    db_session.commit()

    response = client.get("/time/", headers=auth_headers(token, keep.id))
    assert response.status_code == 200
    assert response.json()["current_day"] == 42


# --- Auth tests ---

def test_register_and_login(client: TestClient, db_session: Session):
    """Register a new account, then login"""
    response = client.post("/auth/register", json={"username": "newuser", "password": "testpass1"})
    assert response.status_code == 200
    assert "access_token" in response.json()

    response = client.post("/auth/login", json={"username": "newuser", "password": "testpass1"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_register_duplicate_username(client: TestClient, db_session: Session):
    client.post("/auth/register", json={"username": "dupe", "password": "testpass1"})
    response = client.post("/auth/register", json={"username": "dupe", "password": "testpass1"})
    assert response.status_code == 409

def test_login_wrong_password(client: TestClient, db_session: Session):
    client.post("/auth/register", json={"username": "user1", "password": "correct1"})
    response = client.post("/auth/login", json={"username": "user1", "password": "wrongpass1"})
    assert response.status_code == 401


# --- Keep tests ---

def test_create_keep_seeds_adventurers(client: TestClient, db_session: Session):
    """Creating a keep should seed 6 starting adventurers"""
    response = client.post("/auth/register", json={"username": "keepuser", "password": "testpass1"})
    token = response.json()["access_token"]

    response = client.post(
        "/keeps/",
        json={"name": "Dragon's Rest"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    keep_data = response.json()
    assert keep_data["name"] == "Dragon's Rest"
    assert keep_data["current_day"] == 1

    # Should have 6 adventurers
    adventurers = db_session.query(Adventurer).filter(Adventurer.keep_id == keep_data["id"]).all()
    assert len(adventurers) == 6


# --- Isolation test ---

def test_keeps_are_isolated(client: TestClient, db_session: Session):
    """Adventurers from one keep shouldn't appear in another"""
    account1, keep1, token1 = create_account_and_keep(db_session, "user1", "Keep1")
    account2, keep2, token2 = create_account_and_keep(db_session, "user2", "Keep2")

    create_adventurer_db(db_session, keep1.id, "Adv1", xp=0, gold=0)
    create_adventurer_db(db_session, keep2.id, "Adv2", xp=0, gold=0)

    # User 1 should only see their adventurer
    response = client.get("/adventurers/", headers=auth_headers(token1, keep1.id))
    assert response.status_code == 200
    names = [a["name"] for a in response.json()]
    assert "Adv1" in names
    assert "Adv2" not in names

    # User 2 should only see their adventurer
    response = client.get("/adventurers/", headers=auth_headers(token2, keep2.id))
    assert response.status_code == 200
    names = [a["name"] for a in response.json()]
    assert "Adv2" in names
    assert "Adv1" not in names


# --- Test for POST /parties/ ---
def test_create_party_successful_response(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)
    party_name = "The Mighty Testers"

    response = client.post(
        "/parties/",
        json={"name": party_name},
        headers=auth_headers(token, keep.id),
    )
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == party_name
    assert data["on_expedition"] is False
    assert data["members"] == []
    assert isinstance(data["id"], int)
    assert data["id"] > 0
