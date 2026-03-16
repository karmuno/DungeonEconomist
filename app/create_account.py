"""CLI command to create an account directly in the database.

Usage:
    python -m app.create_account <username> <password> [--admin]
"""
import sys

from app.database import SessionLocal, create_tables
from app.models import Account
from app.auth import hash_password


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    flags = [a for a in sys.argv[1:] if a.startswith('--')]
    is_admin = '--admin' in flags

    if len(args) < 2:
        print("Usage: python -m app.create_account <username> <password> [--admin]")
        sys.exit(1)

    username = args[0]
    password = args[1]

    if len(password) < 4:
        print("Error: Password must be at least 4 characters")
        sys.exit(1)

    create_tables()
    db = SessionLocal()

    existing = db.query(Account).filter(Account.username == username).first()
    if existing:
        if is_admin and not existing.is_admin:
            existing.is_admin = True
            db.commit()
            print(f"Account '{username}' (id={existing.id}) promoted to admin")
        else:
            print(f"Error: Username '{username}' already exists (id={existing.id}, admin={existing.is_admin})")
            sys.exit(1)
        db.close()
        return

    account = Account(
        username=username,
        password_hash=hash_password(password),
        is_admin=is_admin,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    print(f"Account created: id={account.id}, username={account.username}, admin={account.is_admin}")
    db.close()


if __name__ == "__main__":
    main()
