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
_secret = os.environ.get("VENTUREKEEP_SECRET_KEY", "")
if not _secret and os.environ.get("PORT"):
    raise RuntimeError(
        "VENTUREKEEP_SECRET_KEY must be set in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
    )
SECRET_KEY = _secret or "dev-secret-local-only"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(account_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(account_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(account_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(account_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# In-memory revocation set (cleared on restart — acceptable for this scale)
_revoked_tokens: set[str] = set()


def revoke_token(token: str) -> None:
    _revoked_tokens.add(token)


def is_token_revoked(token: str) -> bool:
    return token in _revoked_tokens


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Account:
    """Extract Bearer token, decode JWT, return Account."""
    raw_token = credentials.credentials
    if is_token_revoked(raw_token):
        raise HTTPException(status_code=401, detail="Token has been revoked") from None
    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type") from None
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
