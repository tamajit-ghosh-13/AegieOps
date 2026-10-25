"""Cryptographic and JWT token utilities (AegisOps Slice 6)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import os
from typing import Any
import jwt

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "aegisops-super-secret-key-hackathon-2026")
ALGORITHM = "HS256"
DEFAULT_EXPIRE_MINUTES = 1440  # 24 hours


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Generate salted PBKDF2-SHA256 password hash."""
    salt_val = salt or os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_val.encode("utf-8"),
        100_000,
    ).hex()
    return hashed, salt_val


def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Verify plain password against stored hash and salt."""
    re_hashed, _ = hash_password(plain_password, salt=salt)
    return re_hashed == hashed_password


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Encode JWT bearer access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=DEFAULT_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate JWT bearer token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None
