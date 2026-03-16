from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Keep
from app.auth import get_current_account, get_current_keep

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(account: Account = Depends(get_current_account)) -> Account:
    if not account.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return account


class AdminCommand(BaseModel):
    command: str


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

    if cmd == "add" and len(parts) >= 3:
        return _handle_add(parts[1:], keep, db)

    raise HTTPException(status_code=400, detail=f"Unknown command: {data.command}")


def _handle_add(args: list[str], keep: Keep, db: Session) -> dict:
    resource = args[0].lower()
    try:
        amount = int(args[1])
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid amount: {args[1]}")

    if resource == "gp" or resource == "gold":
        keep.add_treasury(amount * 100)
        db.commit()
        return {"ok": True, "message": f"Added {amount}gp to treasury", "treasury_gold": keep.treasury_gold, "treasury_silver": keep.treasury_silver, "treasury_copper": keep.treasury_copper}

    if resource == "sp" or resource == "silver":
        keep.add_treasury(amount * 10)
        db.commit()
        return {"ok": True, "message": f"Added {amount}sp to treasury", "treasury_gold": keep.treasury_gold, "treasury_silver": keep.treasury_silver, "treasury_copper": keep.treasury_copper}

    if resource == "cp" or resource == "copper":
        keep.add_treasury(amount)
        db.commit()
        return {"ok": True, "message": f"Added {amount}cp to treasury", "treasury_gold": keep.treasury_gold, "treasury_silver": keep.treasury_silver, "treasury_copper": keep.treasury_copper}

    raise HTTPException(status_code=400, detail=f"Unknown resource: {resource}")
