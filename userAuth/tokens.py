"""Session tokens — minimal HS256 JWTs, standard-library only.

Maps to the token the AuthN box in mock-diagram.png hands back after a
successful login. We mint compact, standards-compliant JSON Web Tokens (HS256)
by hand so the mock needs no extra dependency; swap in PyJWT or a real identity
provider later without touching callers — `encode()` / `decode()` keep the same
contract.

The signing secret comes from ``$MECOMMERCE_SECRET``. A dev fallback is used
when it's unset so the app runs out of the box — but that fallback is public, so
tokens signed with it are forgeable. Set the env var in any real deployment.
"""
import base64
import hashlib
import hmac
import json
import os
import time

SECRET = os.environ.get("MECOMMERCE_SECRET", "dev-insecure-secret-change-me").encode()
ALG = "HS256"
TTL_SECONDS = 60 * 60 * 24  # tokens are good for 24h


class TokenError(Exception):
    """Raised when a token is malformed, tampered with, or expired."""


def _b64url_encode(raw: bytes) -> str:
    """Base64url without padding, per the JWT spec."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def _sign(signing_input: bytes) -> str:
    return _b64url_encode(hmac.new(SECRET, signing_input, hashlib.sha256).digest())


def encode(claims: dict, ttl: int = TTL_SECONDS) -> str:
    """Return a signed JWT carrying `claims` plus standard `iat` / `exp`."""
    header = {"alg": ALG, "typ": "JWT"}
    now = int(time.time())
    payload = {**claims, "iat": now, "exp": now + ttl}
    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    segments.append(_sign(signing_input))
    return ".".join(segments)


def decode(token: str) -> dict:
    """Verify signature + expiry and return the claims. Raises TokenError.

    Uses a constant-time signature compare so a bad token can't be distinguished
    from a good one by timing."""
    try:
        header_b64, payload_b64, signature = token.split(".")
    except (ValueError, AttributeError):
        raise TokenError("Malformed token")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    if not hmac.compare_digest(_sign(signing_input), signature):
        raise TokenError("Bad signature")

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, json.JSONDecodeError):
        raise TokenError("Malformed payload")

    if payload.get("exp", 0) < int(time.time()):
        raise TokenError("Token expired")
    return payload
