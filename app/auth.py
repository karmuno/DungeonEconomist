import os
from datetime import datetime, timedelta

import bcrypt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Keep

# Config
SECRET_KEY = os.environ.get("VENTUREKEEP_SECRET_KEY", "dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(account_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(account_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    """Extract Bearer token, decode JWT, return Account."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        account_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=401, detail="Account not found")
    return account


def get_current_keep(
    x_keep_id: int = Header(..., alias="X-Keep-Id"),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> Keep:
    """Read X-Keep-Id header, validate ownership, return Keep."""
    keep = db.query(Keep).filter(Keep.id == x_keep_id, Keep.account_id == account.id).first()
    if not keep:
        raise HTTPException(status_code=404, detail="Keep not found or not owned by this account")
    return keep
