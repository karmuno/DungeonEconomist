from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_account, get_current_keep
from app.database import get_db
from app.magic_items import can_equip, generate_magic_item
from app.models import Account, Adventurer, Keep, MagicItem

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(account: Account = Depends(get_current_account)) -> Account:
    if not account.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return account


class AdminCommand(BaseModel):
    command: str


HELP_TEXT = """Available commands:
  add gp|sp|cp <amount>          — Add currency to treasury
  give item <adv_id> [level]     — Give a random magic item to adventurer (level defaults to 1)
  give xp <adv_id> <amount>      — Grant XP to an adventurer
  test stairs                    — Force a stairs popup on the active expedition
  metrics                        — Toggle the metrics panel (client-side)
  help                           — Show this help"""


@router.post("/exec")
def execute_command(
    data: AdminCommand,
    admin: Account = Depends(require_admin),
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Execute an admin console command."""
    parts = data.command.strip().split()
    if not parts:
        raise HTTPException(status_code=400, detail="Empty command")

    cmd = parts[0].lower()

    if cmd == "help":
        return {"ok": True, "message": HELP_TEXT}

    if cmd == "add" and len(parts) >= 3:
        return _handle_add(parts[1:], keep, db)

    if cmd == "give" and len(parts) >= 3:
        return _handle_give(parts[1:], keep, db)

    if cmd == "test" and len(parts) >= 2 and parts[1] == "stairs":
        return _handle_test_stairs(keep, db)

    raise HTTPException(status_code=400, detail="Unknown command. Type 'help' for available commands.")


def _get_adventurer(adv_id_str: str, keep: Keep, db: Session) -> Adventurer:
    try:
        adv_id = int(adv_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid adventurer ID: {adv_id_str}") from None
    adv = db.query(Adventurer).filter(Adventurer.id == adv_id, Adventurer.keep_id == keep.id).first()
    if not adv:
        raise HTTPException(status_code=404, detail=f"Adventurer #{adv_id} not found")
    return adv


def _handle_add(args: list[str], keep: Keep, db: Session) -> dict:
    resource = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid amount: {args[1]}") from None

    if resource in ("gp", "gold"):
        keep.add_treasury(amount * 100)
        db.commit()
        return {"ok": True, "message": f"Added {amount}gp to treasury"}

    if resource in ("sp", "silver"):
        keep.add_treasury(amount * 10)
        db.commit()
        return {"ok": True, "message": f"Added {amount}sp to treasury"}

    if resource in ("cp", "copper"):
        keep.add_treasury(amount)
        db.commit()
        return {"ok": True, "message": f"Added {amount}cp to treasury"}

    raise HTTPException(status_code=400, detail=f"Unknown resource: {resource}")


def _handle_give(args: list[str], keep: Keep, db: Session) -> dict:
    subcommand = args[0].lower()

    if subcommand == "item" and len(args) >= 2:
        adv = _get_adventurer(args[1], keep, db)
        level = int(args[2]) if len(args) >= 3 else 1
        item = generate_magic_item(level)

        if not can_equip(adv, item["item_type"]):
            # Try the other type
            other_type = "armor" if item["item_type"] == "weapon" else "weapon"
            if can_equip(adv, other_type):
                item = generate_magic_item(level)
                # Force the other type
                item["item_type"] = other_type
                import random

                from app.data.magic_items import _ITEM_DATA
                base = random.choice(_ITEM_DATA["weapons"] if other_type == "weapon" else _ITEM_DATA["armor"])
                item["name"] = f"{item['name'].split()[0]} {base} +{level}"
            else:
                raise HTTPException(status_code=400, detail=f"{adv.name} has no free equipment slots")

        magic_item = MagicItem(
            adventurer_id=adv.id,
            name=item["name"],
            item_type=item["item_type"],
            bonus=item["bonus"],
        )
        db.add(magic_item)
        db.commit()
        return {"ok": True, "message": f"Gave {item['name']} ({item['item_type']}) to {adv.name} (#{adv.id})"}

    if subcommand == "xp" and len(args) >= 3:
        adv = _get_adventurer(args[1], keep, db)
        try:
            amount = int(args[2])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid XP amount: {args[2]}") from None
        adv.xp += amount

        from app.progression import apply_level_ups
        events = []
        apply_level_ups(adv, keep, events)

        db.commit()
        return {
            "ok": True,
            "message": f"Granted {amount} XP to {adv.name} (#{adv.id}). Total: {adv.xp}",
            "events": [e.dict() for e in events],
        }

    raise HTTPException(status_code=400, detail="Unknown give subcommand. Try: give item <id> [level] | give xp <id> <amount>")


def _handle_test_stairs(keep: Keep, db: Session) -> dict:
    """Force a stairs event on the current active expedition for testing."""
    from app.dungeons import DUNGEON_LEVEL_NAMES
    from app.models import Expedition, Party

    active = (
        db.query(Expedition)
        .join(Party, Expedition.party_id == Party.id)
        .filter(
            Party.keep_id == keep.id,
            Expedition.result.in_(["in_progress", "awaiting_choice"]),
        )
        .first()
    )

    if not active:
        raise HTTPException(status_code=400, detail="No active expedition found. Launch a party first.")

    dungeon_level = active.dungeon_level or 1
    total_levels = len(DUNGEON_LEVEL_NAMES)
    next_level = dungeon_level + 1

    if next_level > total_levels:
        raise HTTPException(status_code=400, detail="Party is at max dungeon level — no stairs possible.")

    next_name = DUNGEON_LEVEL_NAMES[dungeon_level] if dungeon_level < total_levels else "the unknown depths"

    stairs_event = {
        "type": "stairs",
        "message": f"Your party discovered stairs down to {next_name}! (Level {next_level}) [TEST]",
        "new_level": next_level,
        "new_level_name": next_name,
        "options": ["press_on_same", "press_on_next", "retreat"],
    }

    active.result = "awaiting_choice"
    active.pending_event = stairs_event
    db.commit()

    party_name = active.party.name if active.party else "Unknown"
    return {
        "ok": True,
        "message": f"Stairs injected into '{party_name}'s expedition.",
        "events": [
            {
                "type": "expedition_choice",
                "message": f"Party '{party_name}': {stairs_event['message']}",
                "expedition_id": active.id,
                "event_subtype": "stairs",
            }
        ],
    }
