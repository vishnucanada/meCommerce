"""AuthN Service — user registration (the "add user" design).

Maps to the "User Auth / AuthN" box in mock-diagram.png. Owns creating users
and would own login/tokens next.

Design decisions per the current spec:
  * Credentials are username + password (no email).
  * All usernames and all passwords are accepted — no format/length rules.
    The only constraint is that a username must be unique (enforced by the
    UNIQUE column in users.db), so re-using one returns 409.
  * Users are persisted in users.db via the database layer. The plaintext
    password never leaves this module; only a salted hash is stored, and the
    API never returns it.

Where YOUR add-user logic goes: drop your own persistence / hashing into
add_user(). The request/response contract stays the same, so the frontend
doesn't change.
"""
import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import db

router = APIRouter(prefix="/api/users", tags=["users"])

PBKDF2_ROUNDS = 100_000

# Mock users seeded into users.db on startup (plaintext here only to seed the
# hash; stored hashed). Handy for demoing login later.
MOCK_USERS = [
    {"username": "aiko", "password": "matcha123"},
    {"username": "kenji", "password": "hojicha"},
    {"username": "admin", "password": "admin"},
]


class NewUser(BaseModel):
    """Registration payload. Plain strings — every value is accepted."""
    username: str
    password: str


class PublicUser(BaseModel):
    """What we send back — no password/hash field."""
    id: str
    username: str
    created_at: str


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Salted PBKDF2-SHA256. Returns 'salt_hex:hash_hex' for storage.
    (For production, prefer a memory-hard KDF like Argon2id / bcrypt.)"""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"{salt.hex()}:{digest.hex()}"


def _create_user(username: str, password: str) -> dict:
    """Build a user row and insert it. The 'add user' core."""
    user = {
        "id": uuid.uuid4().hex,
        "username": username,
        "password_hash": hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert_user(user)  # <-- persistence lives in the database layer
    return user


def seed_mock_users() -> None:
    """Populate users.db with mock accounts if it's empty (idempotent)."""
    if db.count_users() > 0:
        return
    for entry in MOCK_USERS:
        try:
            _create_user(entry["username"], entry["password"])
        except sqlite3.IntegrityError:
            pass  # already there


@router.post("", response_model=PublicUser, status_code=201)
def add_user(payload: NewUser):
    """Create a user. This is the 'add user' entry point."""
    try:
        user = _create_user(payload.username, payload.password)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="That username is already taken.")
    return PublicUser(**user)


@router.get("", response_model=list[PublicUser])
def list_users():
    """Demo/debug endpoint so you can see stored users. Remove or protect this
    once real auth is in place."""
    return [PublicUser(**u) for u in db.list_users()]
