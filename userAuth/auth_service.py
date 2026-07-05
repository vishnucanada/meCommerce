"""AuthN Service — user registration (the "add user" design).

Maps to the "User Auth / AuthN" box in mock-diagram.png. This is the piece you
were building in Python: it owns creating users and would own login/tokens next.

How it embeds with the rest of the backend
-------------------------------------------
- It exposes a router (`POST /api/users`) that `backend/main.py` mounts behind
  the same API, exactly like the Product and Cart services. In a fuller build
  this would be its own deployable service behind the API Gateway.
- The frontend's "Create account" modal POSTs {name, email, password} here.
- Passwords are hashed before storage; the plaintext never leaves this module,
  and the API never returns the hash (see PublicUser).

Where YOUR add-user logic goes
-------------------------------
Replace the in-memory `_users` dict with the SQL "Users and Orders" database
from the diagram, and drop your own validation / hashing / persistence into
`add_user()`. The request/response contract stays the same, so the frontend
doesn't change.
"""
import hashlib
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/api/users", tags=["users"])

# In-memory user store for the mock. Swap for the SQL database (id -> row).
_users: dict[str, dict] = {}

PBKDF2_ROUNDS = 100_000


class NewUser(BaseModel):
    """Validated registration payload. Pydantic rejects bad input with a 422
    before add_user() ever runs, so the handler only sees clean data."""
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class PublicUser(BaseModel):
    """What we send back — note there is no password/hash field."""
    id: str
    name: str
    email: str
    created_at: str


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Salted PBKDF2-SHA256. Returns 'salt_hex:hash_hex' for storage.
    (For production, prefer a memory-hard KDF like Argon2id / bcrypt.)"""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"{salt.hex()}:{digest.hex()}"


def _email_taken(email: str) -> bool:
    return any(u["email"] == email for u in _users.values())


@router.post("", response_model=PublicUser, status_code=201)
def add_user(payload: NewUser):
    """Create a user. This is the 'add user' entry point."""
    email = payload.email.lower()
    if _email_taken(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = {
        "id": uuid.uuid4().hex,
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _users[user["id"]] = user  # <-- replace with an INSERT into the users table
    return PublicUser(**user)


@router.get("", response_model=list[PublicUser])
def list_users():
    """Demo/debug endpoint so you can see created users. Remove or protect
    this once real auth is in place."""
    return [PublicUser(**u) for u in _users.values()]
