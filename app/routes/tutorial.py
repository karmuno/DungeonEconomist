from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_account
from app.database import get_db
from app.models import Account
from app.routes.auth import AccountOut

router = APIRouter(prefix="/tutorial", tags=["tutorial"])

TUTORIAL_COMPLETE = 7


class AdvanceRequest(BaseModel):
    step: int


@router.post("/advance", response_model=AccountOut)
def advance_tutorial(
    data: AdvanceRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> Account:
    """Advance the tutorial step (only moves forward, never backward)."""
    if data.step > account.tutorial_step:
        account.tutorial_step = min(data.step, TUTORIAL_COMPLETE)
        db.commit()
    return account
