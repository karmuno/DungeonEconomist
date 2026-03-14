"""CLI command to create an account directly in the database.

Usage:
    python -m app.create_account <username> <password>
"""
import sys

from app.database import SessionLocal, create_tables
from app.models import Account
from app.auth import hash_password


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m app.create_account <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    if len(password) < 4:
        print("Error: Password must be at least 4 characters")
        sys.exit(1)

    create_tables()
    db = SessionLocal()

    existing = db.query(Account).filter(Account.username == username).first()
    if existing:
        print(f"Error: Username '{username}' already exists (id={existing.id})")
        db.close()
        sys.exit(1)

    account = Account(
        username=username,
        password_hash=hash_password(password),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    print(f"Account created: id={account.id}, username={account.username}")
    db.close()


if __name__ == "__main__":
    main()
