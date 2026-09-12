"""Player events: one row per thing a player did or reached.

The decision gate after the first cohort asks four questions — did they enter the core
loop, where did they leave, did they return, did they reach a death or a level-up — and
this table is what answers them. See buildplans/player-events-spec.md for the event list,
payloads and the gate queries.

Every insert rides the caller's transaction: if the action rolls back, so does the event.
"""
import enum
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Account, Keep, PlayerEvent, PlayerEventType


class EventType(enum.Enum):
    """Every id in the event_types lookup table."""

    ACCOUNT_CREATED = "account_created"
    KEEP_CREATED = "keep_created"
    KEEP_DELETED = "keep_deleted"
    RETURN_SESSION = "return_session"
    PARTY_FORMED = "party_formed"
    EXPEDITION_STARTED = "expedition_started"
    EXPEDITION_DECISION = "expedition_decision"
    EXPEDITION_COMPLETED = "expedition_completed"
    TPK = "tpk"
    ADVENTURER_DIED = "adventurer_died"
    ADVENTURER_LEVELLED = "adventurer_levelled"
    ADVENTURER_BANKRUPT = "adventurer_bankrupt"
    BUILDING_PURCHASED = "building_purchased"
    ADVENTURER_ASSIGNED_TO_BUILDING = "adventurer_assigned_to_building"
    STAIRS_DISCOVERED = "stairs_discovered"
    AUTO_DELVE_TRIGGERED = "auto_delve_triggered"


EVENT_TYPE_DESCRIPTIONS: dict[EventType, str] = {
    EventType.ACCOUNT_CREATED: "Account registered",
    EventType.KEEP_CREATED: "Keep created",
    EventType.KEEP_DELETED: "Keep deleted",
    EventType.RETURN_SESSION: "Came back after an hour or more away",
    EventType.PARTY_FORMED: "Party created",
    EventType.EXPEDITION_STARTED: "Expedition launched, by hand or by auto-delve",
    EventType.EXPEDITION_DECISION: "Choice made at an expedition decision point",
    EventType.EXPEDITION_COMPLETED: "Expedition finalized, returned or retreated",
    EventType.TPK: "Every member of the party died on one expedition",
    EventType.ADVENTURER_DIED: "An adventurer died",
    EventType.ADVENTURER_LEVELLED: "An adventurer gained a level",
    EventType.ADVENTURER_BANKRUPT: "An adventurer went to debtor's prison",
    EventType.BUILDING_PURCHASED: "Building bought or upgraded",
    EventType.ADVENTURER_ASSIGNED_TO_BUILDING: "Adventurer assigned to a building",
    EventType.STAIRS_DISCOVERED: "A deeper dungeon level unlocked",
    EventType.AUTO_DELVE_TRIGGERED: "First time auto-delve launched for this player",
}

RETURN_GAP = timedelta(hours=1)


def log_player_event(
    db: Session,
    event_type: EventType,
    user_id: int,
    keep_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> PlayerEvent:
    """Add one event to the session. The caller commits."""
    event = PlayerEvent(
        event_type_id=event_type.value,
        user_id=user_id,
        keep_id=keep_id,
        payload=payload,
    )
    db.add(event)
    return event


def seed_event_types(db: Session) -> None:
    """Insert any event_types rows that are missing. The migration seeds production; tests call this."""
    existing = {row.id for row in db.query(PlayerEventType.id).all()}
    for event_type, description in EVENT_TYPE_DESCRIPTIONS.items():
        if event_type.value not in existing:
            db.add(PlayerEventType(id=event_type.value, description=description))


def log_return_session(db: Session, account: Account) -> PlayerEvent | None:
    """Record a return if the account's last activity was an hour or more ago.

    Last activity is the newest player_events row for the account, or the account's creation.
    Called from login and refresh only: access tokens last 30 minutes, so anyone away for an
    hour must pass through one of the two. A mid-session refresh fails the gap test and logs
    nothing.
    """
    last_event = (
        db.query(func.max(PlayerEvent.created_at))
        .filter(PlayerEvent.user_id == account.id)
        .scalar()
    )
    last_seen = last_event or account.created_at
    if last_seen is None:
        return None
    gap = datetime.now() - last_seen
    if gap < RETURN_GAP:
        return None
    return log_player_event(
        db,
        EventType.RETURN_SESSION,
        account.id,
        payload={"hours_since_last": round(gap.total_seconds() / 3600, 1)},
    )


def log_first_auto_delve(db: Session, keep: Keep, party_name: str, dungeon_level: int) -> PlayerEvent | None:
    """Record the first auto-delve launch for this player; later ones are ordinary launches."""
    already = (
        db.query(PlayerEvent.id)
        .filter(
            PlayerEvent.user_id == keep.account_id,
            PlayerEvent.event_type_id == EventType.AUTO_DELVE_TRIGGERED.value,
        )
        .first()
    )
    if already:
        return None
    return log_player_event(
        db,
        EventType.AUTO_DELVE_TRIGGERED,
        keep.account_id,
        keep.id,
        {"party_name": party_name, "dungeon_level": dungeon_level},
    )


def wipe_details(replay_log: list[dict]) -> dict[str, Any]:
    """What killed the party: the combat in the turn where the last member died.

    Each combat result carries monster_type and monster_count. When deaths span several
    combats, the wipe is the one that killed the last member.
    """
    last_turn = None
    for turn in replay_log:
        if turn.get("deaths"):
            last_turn = turn
    if last_turn is None:
        return {"monster_type": "Unknown", "monster_count": 0}
    combat = None
    for event in last_turn.get("events", []):
        if event.get("combat"):
            combat = event["combat"]
    if combat is None:
        return {"monster_type": "Unknown", "monster_count": 0}
    return {
        "monster_type": combat.get("monster_type", "Unknown"),
        "monster_count": combat.get("monster_count", 0),
    }
