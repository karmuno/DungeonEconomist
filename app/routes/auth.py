from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_account, hash_password, verify_password
from app.database import get_db
from app.models import Account

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountOut(BaseModel):
    id: int
    username: str
    is_admin: bool = False

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if not data.username.strip() or not data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    if len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

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

    token = create_access_token(account.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.username == data.username.strip()).first()
    if not account or not verify_password(data.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(account.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AccountOut)
def get_me(account: Account = Depends(get_current_account)):
    return account
