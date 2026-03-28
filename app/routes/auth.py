import re

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    get_current_account,
    hash_password,
    revoke_token,
    verify_password,
)
from app.database import get_db
from app.models import Account
from app.rate_limit import auth_rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])

# Minimum 8 chars, at least one letter and one digit
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,}$")


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccountOut(BaseModel):
    id: int
    username: str
    is_admin: bool = False
    tutorial_step: int = 0

    class Config:
        from_attributes = True


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if not _PASSWORD_RE.match(password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one letter and one number",
        )


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    auth_rate_limiter.check(request)

    if not data.username.strip():
        raise HTTPException(status_code=400, detail="Username is required")
    _validate_password(data.password)

    existing = db.query(Account).filter(Account.username == data.username.strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    account = Account(
        username=data.username.strip(),
        password_hash=hash_password(data.password),
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return TokenResponse(
        access_token=create_access_token(account.id, account.token_version),
        refresh_token=create_refresh_token(account.id, account.token_version),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    auth_rate_limiter.check(request)

    account = db.query(Account).filter(Account.username == data.username.strip()).first()
    if not account or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return TokenResponse(
        access_token=create_access_token(account.id, account.token_version),
        refresh_token=create_refresh_token(account.id, account.token_version),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    auth_rate_limiter.check(request)

    try:
        payload = jwt.decode(data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type") from None
        account_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from None

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=401, detail="Account not found")

    # Reject refresh tokens issued before a password change
    token_version = payload.get("tv", 0)
    if token_version != account.token_version:
        raise HTTPException(status_code=401, detail="Token invalidated by password change")

    # Revoke the old refresh token (one-time use)
    revoke_token(data.refresh_token)

    return TokenResponse(
        access_token=create_access_token(account.id, account.token_version),
        refresh_token=create_refresh_token(account.id, account.token_version),
    )


@router.post("/logout")
def logout(request: Request, account: Account = Depends(get_current_account)):
    """Revoke the current access token."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        revoke_token(auth_header[7:])
    return {"detail": "Logged out"}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", response_model=TokenResponse)
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Change password and invalidate all existing sessions."""
    auth_rate_limiter.check(request)

    if not verify_password(data.current_password, account.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    _validate_password(data.new_password)

    account.password_hash = hash_password(data.new_password)
    account.token_version += 1
    db.commit()

    # Return fresh tokens so the current session stays logged in
    return TokenResponse(
        access_token=create_access_token(account.id, account.token_version),
        refresh_token=create_refresh_token(account.id, account.token_version),
    )


@router.get("/me", response_model=AccountOut)
def get_me(account: Account = Depends(get_current_account)):
    return account
