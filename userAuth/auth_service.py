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
import hmac
import os
import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from database import db
from userAuth import tokens

router = APIRouter(prefix="/api/users", tags=["users"])

# Login lives at /api/login (its own box in the diagram's AuthN service), so it
# gets its own router rather than hanging off the /api/users prefix.
auth_router = APIRouter(prefix="/api", tags=["auth"])

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


def verify_password(password: str, stored: str) -> bool:
    """Check a plaintext password against a stored 'salt_hex:hash_hex' value.

    Re-derives the hash with the stored salt and compares in constant time, so a
    wrong password can't be told apart from a right one by timing."""
    try:
        salt_hex, _ = stored.split(":")
        candidate = hash_password(password, bytes.fromhex(salt_hex))
    except ValueError:
        return False
    return hmac.compare_digest(candidate, stored)


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


# --- Login + sessions ----------------------------------------------------
class Credentials(BaseModel):
    """Login payload — same shape as registration."""
    username: str
    password: str


class Session(BaseModel):
    """What login returns: a bearer token and the public user it belongs to."""
    token: str
    user: PublicUser


def _public(user: dict) -> PublicUser:
    return PublicUser(id=user["id"], username=user["username"],
                      created_at=user["created_at"])


@auth_router.post("/login", response_model=Session)
def login(payload: Credentials):
    """Verify credentials and issue a signed session token.

    Returns the same 401 whether the username is unknown or the password is
    wrong, so the endpoint doesn't reveal which usernames exist."""
    user = db.get_user_by_username(payload.username)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = tokens.encode({"sub": user["username"]})
    return Session(token=token, user=_public(user))


# HTTPBearer parses the `Authorization: Bearer <token>` header. auto_error=False
# lets a route stay open to guests (it yields None instead of raising 403).
_bearer = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)


def current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> PublicUser:
    """FastAPI dependency: require a valid token, resolve it to a user."""
    try:
        claims = tokens.decode(creds.credentials)
    except tokens.TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    user = db.get_user_by_username(claims.get("sub", ""))
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return _public(user)


def optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> PublicUser | None:
    """Like current_user, but returns None (instead of 401) when no valid token
    is present — for routes that work for guests and logged-in users alike."""
    if creds is None:
        return None
    try:
        return current_user(creds)
    except HTTPException:
        return None


@router.get("/me", response_model=PublicUser)
def me(user: PublicUser = Depends(current_user)):
    """Return the user the caller's token belongs to (whoami)."""
    return user
