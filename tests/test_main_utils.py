import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import math
from datetime import datetime, timedelta # Added datetime

from app.main import app, get_db
from app.models import Base, Adventurer, GameTime, Party, Expedition
from app.schemas import AdventurerCreate, PartyCreate, GameTimeInfo # Added GameTimeInfo for potential response validation

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
    # Create tables for each test function
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after each test function
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session): # Ensure db_session fixture runs to create tables
    return TestClient(app)

# Helper to create adventurer
def create_adventurer_db(db: Session, name: str, xp: int, gold: int, is_bankrupt: bool = False, expedition_status: str = "resting"):
    adv = Adventurer(
        name=name,
        adventurer_class="Fighter", # Default class for simplicity
        level=1,
        xp=xp,
        gold=gold,
        hp_max=10,
        hp_current=10,
        is_available=True,
        is_bankrupt=is_bankrupt,
        expedition_status=expedition_status
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

# Test Cases

def test_upkeep_successful_payment(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 30)
    adv = create_adventurer_db(db_session, name="TestAdv1", xp=2000, gold=100) # Cost = floor(2000*0.01) = 20

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 80
    assert not adv.is_bankrupt
    assert adv.expedition_status == "resting" # Should not change

    data = response.json()
    assert "Upkeep applied for day 30" in data["message"]
    assert "1 adventurers processed" in data["message"] # Assuming only one adventurer
    assert "0 became bankrupt" in data["message"]
    assert "Total gold deducted: 20 GP" in data["message"]

def test_upkeep_adventurer_goes_bankrupt(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 30)
    adv = create_adventurer_db(db_session, name="TestAdv2", xp=2000, gold=10) # Cost = 20

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 0
    assert adv.is_bankrupt
    assert adv.expedition_status == "Bankrupt"

    data = response.json()
    assert "1 adventurers processed" in data["message"]
    assert "1 became bankrupt" in data["message"]
    assert "Total gold deducted: 10 GP" in data["message"] # Deducted what they had

def test_upkeep_already_bankrupt_cannot_pay(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 60)
    adv = create_adventurer_db(db_session, name="TestAdv3", xp=2000, gold=0, is_bankrupt=True, expedition_status="Bankrupt") # Cost = 20

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 0
    assert adv.is_bankrupt
    assert adv.expedition_status == "Bankrupt"

    data = response.json()
    assert "1 adventurers processed" in data["message"]
    assert "1 became bankrupt" in data["message"] # Still bankrupt
    assert "Total gold deducted: 0 GP" in data["message"]


def test_upkeep_pays_and_clears_bankruptcy(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 90)
    adv = create_adventurer_db(db_session, name="TestAdv4", xp=1000, gold=50, is_bankrupt=True, expedition_status="Bankrupt") # Cost = 10

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 40
    assert not adv.is_bankrupt
    assert adv.expedition_status == "resting" # Default status after clearing bankruptcy

    data = response.json()
    assert "0 became bankrupt" in data["message"] # Cleared bankruptcy
    assert "Total gold deducted: 10 GP" in data["message"]

def test_upkeep_no_upkeep_due_not_day_30(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 29)
    adv = create_adventurer_db(db_session, name="TestAdv5", xp=1000, gold=100)

    initial_gold = adv.gold
    initial_is_bankrupt = adv.is_bankrupt

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == initial_gold
    assert adv.is_bankrupt == initial_is_bankrupt

    data = response.json()
    assert "No upkeep applied for day 29" in data["message"]

def test_upkeep_zero_xp_adventurer(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 30)
    adv = create_adventurer_db(db_session, name="TestAdv6", xp=0, gold=0)

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 0
    assert not adv.is_bankrupt

    data = response.json()
    # Upkeep cost is 0, so no gold deducted, not counted as bankrupt.
    assert "0 became bankrupt" in data["message"]
    assert "Total gold deducted: 0 GP" in data["message"]


def test_bankrupt_adventurer_cannot_launch_expedition(client: TestClient, db_session: Session):
    # Create a party
    party = Party(name="Bankrupt Party")
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    # Create a bankrupt adventurer and add to party
    adv_bankrupt = create_adventurer_db(db_session, name="BankruptAdv", xp=100, gold=0, is_bankrupt=True)
    party.members.append(adv_bankrupt)
    db_session.commit()

    expedition_data = {
        "party_id": party.id,
        "dungeon_level": 1,
        "duration_days": 5
    }
    response = client.post("/expeditions/", data=expedition_data) # Use data for form

    assert response.status_code == 400
    assert "Party contains bankrupt members" in response.json()["detail"]
    assert "BankruptAdv is bankrupt" in response.json()["detail"]

def test_non_bankrupt_party_launches_expedition(client: TestClient, db_session: Session):
    # Create GameTime if needed by expedition logic (e.g. for start_day)
    create_game_time_db(db_session, 1)

    # Create a party
    party = Party(name="Solvent Party")
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    # Create a non-bankrupt adventurer and add to party
    adv_solvent = create_adventurer_db(db_session, name="SolventAdv", xp=100, gold=100, is_bankrupt=False)
    party.members.append(adv_solvent)
    db_session.commit()

    expedition_data = {
        "party_id": party.id,
        "dungeon_level": 1,
        "duration_days": 5
    }
    # This test assumes the basic expedition setup is valid and doesn't require complex supplies etc.
    # The focus is solely on the bankrupt check.
    response = client.post("/expeditions/", data=expedition_data)

    # Expecting success or a different error if other conditions aren't met, but not 400 due to bankruptcy
    assert response.status_code != 400
    # A more specific success code like 200 or 201 would be better if the endpoint always returns that on success.
    # For now, just checking it's not the bankruptcy error.
    # The expedition endpoint returns a complex result, so we'll just check status.
    # If it passed the bankrupt check, it would proceed. The simulator might have its own errors/empty states.
    # Given the current expedition logic, it will run a simulation and return results.
    assert response.status_code == 200 # Expecting the expedition to run
    assert "expedition_id" in response.json()

# Note: More tests could be added for multiple adventurers, some bankrupt, some not, etc.
# And for edge cases like XP being very low (e.g. xp=50, cost=0).
# Test for adv.is_bankrupt reset logic.
def test_upkeep_pays_and_clears_bankruptcy_detailed_status(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 90)
    # Adventurer was bankrupt, now has gold
    adv = create_adventurer_db(db_session, name="AdvClears", xp=1500, gold=100, is_bankrupt=True, expedition_status="Bankrupt") # Cost = 15

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 85
    assert not adv.is_bankrupt
    assert adv.expedition_status == "resting" # Check if status is correctly reset

    data = response.json()
    assert "1 adventurers processed" in data["message"]
    assert "0 became bankrupt" in data["message"] # This means they cleared it
    assert "Total gold deducted: 15 GP" in data["message"]

def test_upkeep_cost_is_zero(client: TestClient, db_session: Session):
    create_game_time_db(db_session, 30)
    # XP is low enough that 1% is < 1, so floor(cost) is 0
    adv = create_adventurer_db(db_session, name="LowXPCost", xp=50, gold=10) # Cost = floor(50*0.01) = 0

    response = client.put("/upkeep")
    assert response.status_code == 200

    db_session.refresh(adv)
    assert adv.gold == 10 # No change
    assert not adv.is_bankrupt

    data = response.json()
    assert "1 adventurers processed" in data["message"]
    assert "0 became bankrupt" in data["message"]
    assert "Total gold deducted: 0 GP" in data["message"]

# Initialize GameTime if it doesn't exist in /upkeep
def test_upkeep_initializes_gametime(client: TestClient, db_session: Session):
    # No GameTime created initially
    adv = create_adventurer_db(db_session, name="AdvGametimeInit", xp=1000, gold=100)

    response = client.put("/upkeep") # Should run on day 1 (default init) if GT doesn't exist
    assert response.status_code == 200

    game_time = db_session.query(GameTime).first()
    assert game_time is not None
    assert game_time.current_day == 1 # Default init

    data = response.json()
    assert "No upkeep applied for day 1" in data["message"] # Day 1 is not a multiple of 30

    db_session.refresh(adv)
    assert adv.gold == 100 # No change as no upkeep on day 1
    assert not adv.is_bankrupt

    # Now set day to 30 and try again
    game_time.current_day = 30
    db_session.commit()

    response_day30 = client.put("/upkeep")
    assert response_day30.status_code == 200
    data_day30 = response_day30.json()
    assert "Upkeep applied for day 30" in data_day30["message"]
    assert "Total gold deducted: 10 GP" in data_day30["message"] # Cost for 1000 XP

    db_session.refresh(adv)
    assert adv.gold == 90

# TODO: Add tests for expedition balancing in a separate file or below if structure allows.
# For now, focusing on upkeep and bankruptcy launch prevention.


# --- Tests for /time/advance-day ---

def test_advance_day_existing_gametime(client: TestClient, db_session: Session):
    initial_datetime = datetime.now() - timedelta(hours=1)
    gt = GameTime(current_day=5, day_started_at=initial_datetime, last_updated=initial_datetime)
    db_session.add(gt)
    db_session.commit()
    db_session.refresh(gt)

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    data = response.json()
    assert data["current_day"] == 6

    # Parse datetimes for comparison
    response_last_updated = datetime.fromisoformat(data["last_updated"])
    assert response_last_updated > initial_datetime

    db_game_time = db_session.query(GameTime).first()
    assert db_game_time is not None
    assert db_game_time.current_day == 6
    assert db_game_time.last_updated == response_last_updated # Check if DB matches response dt

def test_advance_day_no_initial_gametime(client: TestClient, db_session: Session):
    # Ensure no GameTime exists
    assert db_session.query(GameTime).first() is None

    response = client.post("/time/advance-day")
    assert response.status_code == 200

    data = response.json()
    assert data["current_day"] == 1 # Initialized at 0, then incremented
    assert "last_updated" in data

    db_game_time = db_session.query(GameTime).first()
    assert db_game_time is not None
    assert db_game_time.current_day == 1
    assert datetime.fromisoformat(data["last_updated"]) == db_game_time.last_updated

def test_advance_day_multiple_advances(client: TestClient, db_session: Session):
    # Start with no GameTime
    initial_day_check = 0

    # Or start with existing GameTime
    # create_game_time_db(db_session, 10)
    # initial_day_check = 10

    for i in range(1, 4): # Call 3 times
        response = client.post("/time/advance-day")
        assert response.status_code == 200
        data = response.json()
        assert data["current_day"] == initial_day_check + i

    db_game_time = db_session.query(GameTime).first()
    assert db_game_time is not None
    assert db_game_time.current_day == initial_day_check + 3

def test_advance_day_multiple_advances_from_existing(client: TestClient, db_session: Session):
    initial_day = 10
    create_game_time_db(db_session, initial_day)

    for i in range(1, 4): # Call 3 times
        response = client.post("/time/advance-day")
        assert response.status_code == 200
        data = response.json()
        assert data["current_day"] == initial_day + i

    db_game_time = db_session.query(GameTime).first()
    assert db_game_time is not None
    assert db_game_time.current_day == initial_day + 3

# --- Test for POST /parties/ ---
def test_create_party_successful_response(client: TestClient, db_session: Session):
    party_name = "The Mighty Testers"
    party_funds = 123

    response = client.post("/parties/", data={"name": party_name, "funds": party_funds})
    assert response.status_code == 200

    data = response.json()

    # Check top-level keys (example, can be more comprehensive)
    expected_keys = ["id", "name", "created_at", "on_expedition", "current_expedition_id", "funds", "player_id", "members", "supplies"]
    for key in expected_keys:
        assert key in data, f"Key '{key}' missing in response"

    assert data["name"] == party_name
    assert data["funds"] == party_funds
    assert data["on_expedition"] is False # Default for new party
    assert data["members"] == [] # Should be empty for a new party
    assert data["supplies"] is None # Based on PartyOut schema: Optional[List[PartySupplyOut]] = None

    assert isinstance(data["id"], int)
    assert data["id"] > 0 # Should have a positive ID from DB

    # Check created_at is a valid ISO datetime string
    try:
        datetime.fromisoformat(data["created_at"])
    except ValueError:
        pytest.fail(f"created_at '{data['created_at']}' is not a valid ISO datetime string")

    # Verify in DB
    db_party = db_session.query(Party).filter(Party.id == data["id"]).first()
    assert db_party is not None
    assert db_party.name == party_name
    assert db_party.funds == party_funds
    assert not db_party.on_expedition
    assert len(db_party.members) == 0
    # SQLAlchemy default for empty relationship is an empty list, Pydantic might serialize it to None or [] based on schema
    # The explicit loading in create_party should ensure these are at least initialized as empty collections.
    # For `supplies` which is backref from `Supply` to `Party` via `party_supply` table,
    # and PartyOut has `supplies: Optional[List[PartySupplyOut]] = None`,
    # if no supplies are added, it should be None or an empty list.
    # The explicit `_ = new_party.supplies` should ensure the attribute is accessed.
    # If Party.supplies is a standard relationship(), it will be an empty list.
    # If it's from a backref on Supply.parties, it might depend on how it's set up.
    # Given PartyOut.supplies is Optional and defaults to None, None is the most likely correct value if empty.
    assert db_party.supplies == [] # SQLAlchemy relationships are typically empty lists if not populated.
                                 # Pydantic serialization to None for response is fine due to Optional schema.
