"""In-game feedback for the playtest cohort.

One POST, reachable signed in or not. See buildplans/feedback-form-spec.md and the
design handoff it was built from.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import get_current_account
from app.database import get_db
from app.models import Account, Feedback, Keep
from app.rate_limit import RateLimiter
from app.schemas import FeedbackCreate, FeedbackOut

router = APIRouter()

# Anyone can submit, so the endpoint is throttled like the auth endpoints are.
feedback_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)

_optional_bearer = HTTPBearer(auto_error=False)


def get_optional_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    db: Session = Depends(get_db),
) -> Account | None:
    """The signed-in account when the request carries a good token; None otherwise, never a 401.

    Feedback from a stale session is still feedback, so a bad token is treated as anonymous.
    """
    if credentials is None:
        return None
    try:
        return get_current_account(credentials, db)
    except HTTPException:
        return None


@router.post("/feedback/", response_model=FeedbackOut)
def submit_feedback(
    data: FeedbackCreate,
    request: Request,
    x_keep_id: int | None = Header(None, alias="X-Keep-Id"),
    account: Account | None = Depends(get_optional_account),
    db: Session = Depends(get_db),
) -> FeedbackOut:
    """Store one piece of feedback. The server stamps who, which keep, and when."""
    feedback_rate_limiter.check(request)

    keep_id = None
    if account is not None and x_keep_id is not None:
        keep = db.query(Keep).filter(Keep.id == x_keep_id, Keep.account_id == account.id).first()
        keep_id = keep.id if keep else None

    # The name field only exists for visitors; a signed-in player is identified by the account.
    name = None
    if account is None and data.name and data.name.strip():
        name = data.name.strip()

    row = Feedback(
        user_id=account.id if account else None,
        keep_id=keep_id,
        category=data.category,
        doing=data.doing.strip(),
        feedback=data.feedback.strip(),
        severity=data.severity,
        name=name,
        page_url=data.page_url,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return FeedbackOut(id=row.id)
