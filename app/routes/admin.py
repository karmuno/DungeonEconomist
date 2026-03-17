from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Keep, Adventurer, MagicItem
from app.auth import get_current_account, get_current_keep
from app.magic_items import generate_magic_item, can_equip

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

    raise HTTPException(status_code=400, detail=f"Unknown command. Type 'help' for available commands.")


def _get_adventurer(adv_id_str: str, keep: Keep, db: Session) -> Adventurer:
    try:
        adv_id = int(adv_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid adventurer ID: {adv_id_str}")
    adv = db.query(Adventurer).filter(Adventurer.id == adv_id, Adventurer.keep_id == keep.id).first()
    if not adv:
        raise HTTPException(status_code=404, detail=f"Adventurer #{adv_id} not found")
    return adv


def _handle_add(args: list[str], keep: Keep, db: Session) -> dict:
    resource = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid amount: {args[1]}")

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
                from app.data.magic_items import _ITEM_DATA
                import random
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
            raise HTTPException(status_code=400, detail=f"Invalid XP amount: {args[2]}")
        adv.xp += amount
        db.commit()
        return {"ok": True, "message": f"Granted {amount} XP to {adv.name} (#{adv.id}). Total: {adv.xp}"}

    raise HTTPException(status_code=400, detail=f"Unknown give subcommand. Try: give item <id> [level] | give xp <id> <amount>")
