import math
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models import Account, Adventurer, AdventurerClass, Base, Expedition, Keep, Party

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


def test_admin_console_rejects_non_admin(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)

    response = client.post(
        "/admin/exec", json={"command": "add gp 5"}, headers=auth_headers(token, keep.id)
    )
    assert response.status_code == 403


def test_admin_console_open_env_flag_allows_non_admin(client: TestClient, db_session: Session, monkeypatch):
    monkeypatch.setenv("ADMIN_CONSOLE_OPEN", "true")
    account, keep, token = create_account_and_keep(db_session)

    response = client.post(
        "/admin/exec", json={"command": "add gp 5"}, headers=auth_headers(token, keep.id)
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True

    me = client.get("/auth/me", headers=auth_headers(token, keep.id))
    assert me.status_code == 200
    assert me.json()["admin_console_open"] is True


def test_tpk_finalize_marks_all_members_dead(client: TestClient, db_session: Session):
    """Regression: mutating party.members while iterating skipped every other
    member on a TPK, leaving 'survivors' the sim had killed."""
    account, keep, token = create_account_and_keep(db_session)

    party = Party(name="Doomed Six", keep_id=keep.id)
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    members = [
        create_adventurer_db(db_session, keep.id, name=f"Doomed{i}", xp=0, gold=0)
        for i in range(6)
    ]
    for m in members:
        party.members.append(m)
    db_session.commit()

    from app.models import Expedition
    exp = Expedition(
        party_id=party.id,
        start_day=keep.current_day,
        duration_days=3,
        return_day=keep.current_day + 2,
        dungeon_level=1,
        result="in_progress",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    from app.routes.expeditions import _finalize_expedition
    sim = {
        "dead_members": [m.name for m in members],
        "log": [],
        "starting_hp": {},
        "treasure_total": 0,
        "treasure_silver": 0,
        "treasure_copper": 0,
        "xp_per_party_member": 0,
        "special_items": [],
    }
    _finalize_expedition(exp, sim, db_session, keep)
    db_session.commit()

    for m in members:
        db_session.refresh(m)
        assert m.is_dead, f"{m.name} should be dead after a TPK"
    db_session.refresh(party)
    assert len(party.members) == 0


def test_active_summary_hides_unwitnessed_turns(client: TestClient, db_session: Session):
    """Regression: the pre-simulated run must not leak future turns. Before a
    decision point fires, the active summary shows nothing; once the pending
    event is on screen (awaiting_choice) its turn becomes visible."""
    account, keep, token = create_account_and_keep(db_session)
    party = Party(name="Peekers", keep_id=keep.id)
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    from app.models import Expedition
    sim = {
        "log": [
            {"turn": 1, "events": [{"type": "Monster"}], "deaths": []},
            {"turn": 2, "events": [{"type": "Monster"}], "deaths": ["Someone"]},
        ],
        "decision_points": [{"after_turn": 2, "type": "death", "message": "x"}],
        "turn_summaries": ["Turn 1: fight", "Turn 2: deaths"],
        "starting_hp": {},
        "starting_spells": 4,
        "starting_heals": 2,
        "spells_left": 0,
        "heals_left": 0,
        "phases": [{"loot": 5, "silver": 0, "copper": 0, "xp": 100, "deaths": ["Someone"]}],
    }
    exp = Expedition(
        party_id=party.id,
        start_day=keep.current_day,
        duration_days=3,
        return_day=keep.current_day + 2,
        dungeon_level=1,
        result="in_progress",
        resolved_phases=0,
        simulation_data=sim,
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    from app.routes.expeditions import _build_active_summary

    # Nothing witnessed yet: no turns, no summaries
    summary = _build_active_summary(exp, party, keep)
    assert summary["events_log"] == []
    assert summary["turn_summaries"] == []
    # Resources show the launch snapshot, never end-of-run leftovers
    assert summary["spells_left"] == 4
    assert summary["heals_left"] == 2
    # Pending phase totals and deaths stay hidden too
    assert summary["total_xp"] == 0
    assert summary["total_loot"] == 0

    # The decision point fires: its turn (and everything before) is visible
    exp.result = "awaiting_choice"
    summary = _build_active_summary(exp, party, keep)
    assert [t["turn"] for t in summary["events_log"]] == [1, 2]
    assert summary["turn_summaries"] == ["Turn 1: fight", "Turn 2: deaths"]
    assert summary["total_xp"] == 100
    assert summary["total_loot"] == 5


# ── Upkeep while away ────────────────────────────────────────────────────────

_QUIET_SIM = {
    "log": [],
    "starting_hp": {},
    "dead_members": [],
    "treasure_total": 0,
    "treasure_silver": 0,
    "treasure_copper": 0,
    "xp_earned": 0,
    "xp_per_party_member": 0,
    "special_items": [],
    "decision_points": [],
    "phases": [],
}


def _party_away(db: Session, keep, start_day: int, return_day: int, sim: dict, gold: int = 100):
    """Three 2000-XP adventurers (100gp each by default) out on an uneventful expedition."""
    from app.models import Expedition

    party = Party(name="Away Team", keep_id=keep.id, on_expedition=True)
    db.add(party)
    db.commit()
    members = [create_adventurer_db(db, keep.id, name=f"Away{i}", xp=2000, gold=gold) for i in range(3)]
    for m in members:
        m.on_expedition = True
        party.members.append(m)
    exp = Expedition(
        party_id=party.id,
        start_day=start_day,
        duration_days=return_day - start_day + 1,
        return_day=return_day,
        dungeon_level=1,
        result="in_progress",
        resolved_phases=0,
        simulation_data=sim,
    )
    db.add(exp)
    db.commit()
    party.current_expedition_id = exp.id
    db.commit()
    return party, members, exp


def _upkeep_event(events: list[dict]) -> dict | None:
    return next((e for e in events if e["type"] == "upkeep" and e.get("data")), None)


def test_adventurers_in_the_dungeon_pay_upkeep_on_the_day(client: TestClient, db_session: Session):
    """No deferral: a party out over day 30 pays on day 30 like everyone else,
    and nothing more is collected when it comes home."""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 29
    db_session.commit()
    party, members, exp = _party_away(db_session, keep, start_day=29, return_day=31, sim=_QUIET_SIM)

    day30 = client.post("/time/advance-day", headers=auth_headers(token, keep.id)).json()["events"]
    ledger = _upkeep_event(day30)
    assert ledger is not None
    assert sorted(r["name"] for r in ledger["data"]["rows"]) == ["Away0", "Away1", "Away2"]
    assert all(r["outcome"] == "paid" and r["upkeep_cp"] == 2000 for r in ledger["data"]["rows"])
    assert ledger["data"]["collected_cp"] == 6000
    assert "deferred" not in ledger["data"]
    db_session.refresh(keep)
    assert keep.treasury_total_copper() == 6000

    day31 = client.post("/time/advance-day", headers=auth_headers(token, keep.id)).json()["events"]
    assert any(e["type"] == "expedition_complete" for e in day31)
    assert not any(e["type"].startswith("upkeep") for e in day31)
    db_session.refresh(keep)
    assert keep.treasury_total_copper() == 6000
    for m in members:
        db_session.refresh(m)
        assert m.total_copper() == 10000 - 2000


def test_short_adventurers_in_the_dungeon_settle_on_return(client: TestClient, db_session: Session):
    """Can't cover upkeep while away: they pay what they have on the day and
    carry the rest. Loot on return covers it, so nobody goes to prison."""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 29
    db_session.commit()
    sim = {**_QUIET_SIM, "treasure_total": 90}  # 90gp split three ways = 30gp each
    party, members, exp = _party_away(db_session, keep, start_day=29, return_day=31, sim=sim, gold=10)

    day30 = client.post("/time/advance-day", headers=auth_headers(token, keep.id)).json()["events"]
    ledger = _upkeep_event(day30)
    assert all(r["outcome"] == "owed" for r in ledger["data"]["rows"])
    assert ledger["data"]["prison_names"] == []
    db_session.refresh(keep)
    assert keep.treasury_total_copper() == 3 * 1000  # the 10gp each they had
    for m in members:
        db_session.refresh(m)
        assert m.upkeep_debt_cp == 1000 and m.total_copper() == 0 and not m.is_bankrupt

    day31 = client.post("/time/advance-day", headers=auth_headers(token, keep.id)).json()["events"]
    assert sum("paid 10gp in overdue upkeep" in e["message"] for e in day31) == 3
    db_session.refresh(keep)
    assert keep.treasury_total_copper() == 3 * 2000
    for m in members:
        db_session.refresh(m)
        assert m.upkeep_debt_cp == 0 and m.total_copper() == 3000 - 1000 and not m.is_bankrupt


def test_short_adventurers_with_no_loot_go_to_prison_on_return(client: TestClient, db_session: Session):
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 29
    db_session.commit()
    party, members, exp = _party_away(db_session, keep, start_day=29, return_day=31, sim=_QUIET_SIM, gold=0)

    client.post("/time/advance-day", headers=auth_headers(token, keep.id))  # day 30: owed
    day31 = client.post("/time/advance-day", headers=auth_headers(token, keep.id)).json()["events"]
    assert sum("sent to debtor's prison" in e["message"] for e in day31) == 3
    for m in members:
        db_session.refresh(m)
        assert m.is_bankrupt and m.bankruptcy_day == 31 and m.upkeep_debt_cp == 0


def test_disbanded_party_keeps_its_expeditions(client: TestClient, db_session: Session):
    """Removing the last member disbands the party; it leaves the party list
    but its expedition still shows on the Expeditions tab."""
    account, keep, token = create_account_and_keep(db_session)
    party = Party(name="Old Guard", keep_id=keep.id)
    db_session.add(party)
    db_session.commit()
    adv = create_adventurer_db(db_session, keep.id, name="Last One", xp=0, gold=0)
    party.members.append(adv)
    from app.models import Expedition
    exp = Expedition(
        party_id=party.id, start_day=1, duration_days=3, return_day=3, dungeon_level=1,
        result="completed", simulation_data=_QUIET_SIM,
    )
    db_session.add(exp)
    db_session.commit()

    r = client.post(
        "/parties/remove-member/",
        json={"party_id": party.id, "adventurer_id": adv.id},
        headers=auth_headers(token, keep.id),
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"deleted": True, "party_id": party.id}

    parties = client.get("/parties/", headers=auth_headers(token, keep.id)).json()
    assert [p["name"] for p in parties] == []
    expeditions = client.get("/expeditions/", headers=auth_headers(token, keep.id)).json()
    assert [(e["id"], e["party_name"]) for e in expeditions] == [(exp.id, "Old Guard")]


# ── Character sheet: to-hit and class abilities ─────────────────────────────

def _cleric(db: Session, keep_id: int, level: int) -> Adventurer:
    adv = Adventurer(
        keep_id=keep_id,
        name=f"Cleric{level}",
        adventurer_class=AdventurerClass.CLERIC,
        level=level,
        xp=0,
        gold=0,
        hp_max=10,
        hp_current=10,
        is_available=True,
    )
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return adv


def test_sheet_to_hit_is_one_d20_number(client: TestClient, db_session: Session):
    """THAC0 19 reads as +1; the class bonus is folded in: Fighter L1 = +2, Cleric L1 = +1."""
    account, keep, token = create_account_and_keep(db_session)
    fighter = create_adventurer_db(db_session, keep.id, name="Bram", xp=0, gold=0)
    cleric = _cleric(db_session, keep.id, level=1)

    f = client.get(f"/adventurers/{fighter.id}", headers=auth_headers(token, keep.id)).json()
    c = client.get(f"/adventurers/{cleric.id}", headers=auth_headers(token, keep.id)).json()
    assert f["thac0"] == 19 and f["to_hit_bonus"] == 1 and f["to_hit"] == 2
    assert c["thac0"] == 19 and c["to_hit_bonus"] == 0 and c["to_hit"] == 1


def test_sheet_abilities_unlock_by_level_with_uses(client: TestClient, db_session: Session):
    """A level-1 Cleric shows only Turn Undead; at level 4 Revive and Cure appear with level/2 uses."""
    account, keep, token = create_account_and_keep(db_session)
    lvl1 = _cleric(db_session, keep.id, level=1)
    lvl4 = _cleric(db_session, keep.id, level=4)

    a1 = client.get(f"/adventurers/{lvl1.id}", headers=auth_headers(token, keep.id)).json()["class_abilities"]
    assert [a["name"] for a in a1] == ["Turn Undead"]
    assert a1[0]["uses"] == 1

    a4 = client.get(f"/adventurers/{lvl4.id}", headers=auth_headers(token, keep.id)).json()["class_abilities"]
    assert [a["name"] for a in a4] == ["Turn Undead", "Revive", "Cure Light Wounds"]
    assert [a["uses"] for a in a4] == [4, 2, 2]

    # Passive abilities carry no count; Fighters have none at all
    fighter = create_adventurer_db(db_session, keep.id, name="Bram", xp=0, gold=0)
    assert client.get(f"/adventurers/{fighter.id}", headers=auth_headers(token, keep.id)).json()["class_abilities"] == []


def _retreating_expedition(db: Session, keep: Keep, adv: Adventurer, xp: int = 20) -> Expedition:
    """A 7-day expedition sitting on its first decision point, ready to retreat."""
    party = Party(keep_id=keep.id, name="The Bold", on_expedition=True)
    db.add(party)
    db.commit()
    party.members.append(adv)
    adv.on_expedition = True
    db.commit()

    decision_point = {"type": "big_haul", "message": "A heavy chest", "after_turn": 1}
    expedition = Expedition(
        party_id=party.id,
        start_day=keep.current_day,
        duration_days=7,
        return_day=keep.current_day + 6,
        dungeon_level=1,
        result="awaiting_choice",
        pending_event=decision_point,
        resolved_phases=0,
        decision_day=keep.current_day,
        started_at=datetime.now(),
        simulation_data={
            "phases": [{"loot": 10, "silver": 0, "copper": 0, "xp": xp, "deaths": []}],
            "decision_points": [decision_point],
            "log": [{"turn": 1, "events": [], "deaths": []}],
            "turn_summaries": ["Turn 1"],
            "starting_hp": {adv.name: adv.hp_max},
            "party_status": {"members_total": 1},
            "treasure_total": 99,
            "xp_earned": 99,
        },
    )
    db.add(expedition)
    db.commit()
    db.refresh(expedition)
    party.current_expedition_id = expedition.id
    db.commit()
    return expedition


def test_early_retreat_reports_the_day_the_party_came_home(client: TestClient, db_session: Session):
    """Retreating on day 3 of a 7-day plan must not report the planned day 7 end."""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 10
    db_session.commit()
    adv = create_adventurer_db(db_session, keep.id, name="Rurik", xp=0, gold=0)
    expedition = _retreating_expedition(db_session, keep, adv)
    planned_return = expedition.return_day

    # Retreat three days in
    keep.current_day = 12
    db_session.commit()
    headers = auth_headers(token, keep.id)
    resp = client.post(f"/expeditions/{expedition.id}/choose", json={"choice": "retreat"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["retreated"] is True

    summary = client.get(f"/expeditions/{expedition.id}/summary", headers=headers).json()
    assert summary["return_day"] == planned_return
    assert summary["actual_return_day"] == 12

    listed = next(e for e in client.get("/expeditions/", headers=headers).json() if e["id"] == expedition.id)
    assert listed["actual_return_day"] == 12

    detail = client.get(f"/expeditions/{expedition.id}", headers=headers).json()
    assert detail["actual_return_day"] == 12


def test_expedition_run_to_completion_has_no_actual_return_day(client: TestClient, db_session: Session):
    """A party that presses on to the planned end reports no separate actual date."""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 10
    db_session.commit()
    adv = create_adventurer_db(db_session, keep.id, name="Rurik", xp=0, gold=0)
    expedition = _retreating_expedition(db_session, keep, adv)
    headers = auth_headers(token, keep.id)

    resp = client.post(f"/expeditions/{expedition.id}/choose", json={"choice": "press_on"}, headers=headers)
    assert resp.status_code == 200, resp.text

    listed = next(e for e in client.get("/expeditions/", headers=headers).json() if e["id"] == expedition.id)
    assert listed["actual_return_day"] is None


def test_adventurer_levels_up_the_moment_expedition_xp_lands(client: TestClient, db_session: Session):
    """Enough XP to level must advance the adventurer in the same response, not at end of day."""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 10
    db_session.commit()
    adv = create_adventurer_db(db_session, keep.id, name="Rurik", xp=0, gold=0)
    assert adv.level == 1
    expedition = _retreating_expedition(db_session, keep, adv, xp=5000)
    headers = auth_headers(token, keep.id)

    resp = client.post(f"/expeditions/{expedition.id}/choose", json={"choice": "retreat"}, headers=headers)
    assert resp.status_code == 200, resp.text

    # Levelled before the day ever advanced
    db_session.refresh(adv)
    assert adv.level > 1
    assert keep.current_day == 10

    level_ups = [e for e in resp.json()["events"] if e["type"] == "level_up"]
    assert level_ups, resp.json()["events"]
    assert "Rurik" in level_ups[0]["message"]


def test_level_up_event_links_to_the_adventurer(client: TestClient, db_session: Session):
    """Every level-up event names the adventurer and carries their id for the sheet link."""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 10
    db_session.commit()
    adv = create_adventurer_db(db_session, keep.id, name="Rurik", xp=0, gold=0)
    expedition = _retreating_expedition(db_session, keep, adv, xp=5000)
    headers = auth_headers(token, keep.id)

    resp = client.post(f"/expeditions/{expedition.id}/choose", json={"choice": "retreat"}, headers=headers)
    level_ups = [e for e in resp.json()["events"] if e["type"] == "level_up"]
    assert level_ups
    assert level_ups[0]["adventurers"] == [{"id": adv.id, "name": "Rurik"}]


def test_events_naming_an_adventurer_carry_their_id(client: TestClient, db_session: Session):
    """Any event whose message names an adventurer must carry a ref the UI can link."""
    account, keep, token = create_account_and_keep(db_session)
    keep.current_day = 10
    db_session.commit()
    hurt = create_adventurer_db(db_session, keep.id, name="Bram", xp=0, gold=0)
    hurt.hp_current = hurt.hp_max - 1
    db_session.commit()

    resp = client.post("/time/advance-day", headers=auth_headers(token, keep.id))
    assert resp.status_code == 200, resp.text
    events = resp.json()["events"]

    named = [e for e in events if e["type"] in ("healing", "recruitment", "level_up", "death")]
    assert named, events
    for event in named:
        assert event["adventurers"], f"no adventurer ref on: {event}"
        for ref in event["adventurers"]:
            assert isinstance(ref["id"], int)
            assert ref["name"] in event["message"]


# --- Ghost adventurers: the simulator must see today's roster, not the first launch's ---

def test_relaunch_simulates_the_current_roster(client: TestClient, db_session: Session):
    """A second launch with the same first member simulates the party as it stands now.

    The simulator is process-global. launch_expedition used to reuse the party it had
    registered at that party's first launch (matched on the first member's id), so every
    later expedition fought with the dead at their original HP and level — expeditions
    891 and 892 in the 2026-09-09 save."""
    from app.models import Expedition

    account, keep, token = create_account_and_keep(db_session)
    party = Party(name="Stat Testers", keep_id=keep.id)
    db_session.add(party)
    db_session.commit()
    db_session.refresh(party)

    leader = create_adventurer_db(db_session, keep.id, name="Aldric", xp=100, gold=100)
    doomed = create_adventurer_db(db_session, keep.id, name="Faust", xp=100, gold=100)
    party.members.extend([leader, doomed])
    db_session.commit()

    headers = auth_headers(token, keep.id)
    first = client.post("/expeditions/", json={"party_id": party.id, "dungeon_level": 1}, headers=headers)
    assert first.status_code == 200
    db_session.expire_all()
    first_exp = db_session.get(Expedition, first.json()["expedition_id"])
    assert first_exp.simulation_data["party_status"]["members_total"] == 2

    # Faust dies, the party comes home, two recruits join. Same leader, new roster.
    first_exp.result = "completed"
    party.on_expedition = False
    party.current_expedition_id = None
    doomed.is_dead = True
    party.members.remove(doomed)
    leader.on_expedition = False
    leader.is_available = True
    recruits = [create_adventurer_db(db_session, keep.id, name=n, xp=100, gold=100) for n in ("Borin", "Yorick")]
    party.members.extend(recruits)
    db_session.commit()

    second = client.post("/expeditions/", json={"party_id": party.id, "dungeon_level": 1}, headers=headers)
    assert second.status_code == 200
    db_session.expire_all()
    second_exp = db_session.get(Expedition, second.json()["expedition_id"])
    assert second_exp.simulation_data["party_status"]["members_total"] == 3
    assert set(second_exp.simulation_data["starting_hp"]) == {"Aldric", "Borin", "Yorick"}
