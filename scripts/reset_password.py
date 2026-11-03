"""Give a locked-out player a new password.

Accounts have no email, so there is no self-serve reset; until there is, this is how a player
who lost their password gets back in. It sets a new random password, prints it once to hand
to the player privately, and ends every session the account has open, the same way
/auth/change-password does.

Reads whatever database `DATABASE_URL` points at, falling back to the local SQLite file
exactly as the app does.

    python scripts/reset_password.py <username>

On the server, as the venturekeep user, the image has no scripts/, so mount it:

    docker run --rm --network venturekeep-net --env-file ~/venturekeep/.env \\
      -v ~/venturekeep/scripts:/app/scripts:ro venturekeep:latest \\
      python scripts/reset_password.py <username>
"""

import argparse
import secrets
import string
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy.orm import Session  # noqa: E402

from app.auth import hash_password  # noqa: E402  (importing app also loads .env)
from app.database import SessionLocal  # noqa: E402
from app.models import Account  # noqa: E402

# Letters and digits, minus the ones that are easy to misread when copied by hand: I l 1 O o 0
ALPHABET = "".join(c for c in string.ascii_letters + string.digits if c not in "Il1Oo0")


def new_password(length: int = 16) -> str:
    """A random password that passes the sign-up rule: at least one letter and one number."""
    while True:
        password = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if any(c.isalpha() for c in password) and any(c.isdigit() for c in password):
            return password


def reset_password(db: Session, username: str) -> str | None:
    """Set a new random password and end the account's sessions. None if no such account."""
    account = db.query(Account).filter(Account.username == username.strip()).first()
    if account is None:
        return None
    password = new_password()
    account.password_hash = hash_password(password)
    account.token_version += 1
    db.commit()
    return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Give a locked-out player a new password.")
    parser.add_argument("username")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        password = reset_password(db, args.username)
    finally:
        db.close()

    if password is None:
        print(f"No account named {args.username!r}", file=sys.stderr)
        return 1
    print(f"New password for {args.username}: {password}")
    print("Their open sessions have ended. Send it to them privately.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
