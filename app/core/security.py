from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
MAX_PASSWORD_BYTES = 100  # bcrypt limitation


@lru_cache(maxsize=1)
def get_private_key() -> str:
    key_path = settings.private_key_path
    if not key_path.exists():
        raise FileNotFoundError(
            f"Private key not found at {
                key_path
            }. Run `python -m app.cli generate-keys` first."
        )
    return key_path.read_text()


@lru_cache(maxsize=1)
def get_public_key() -> str:
    key_path = settings.public_key_path
    if not key_path.exists():
        raise FileNotFoundError(
            f"Public key not found at {
                key_path
            }. Run `python -m app.cli generate-keys` first."
        )
    return key_path.read_text()


def reset_key_cache() -> None:
    get_private_key.cache_clear()
    get_public_key.cache_clear()


def _ensure_password_length(password: str) -> None:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError("Password cannot exceed 72 bytes due to bcrypt limitations.")


def hash_password(password: str) -> str:
    _ensure_password_length(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        _ensure_password_length(plain_password)
    except ValueError:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        return False


def create_access_token(
    *,
    subject: str,
    role: str,
    permissions: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "role": role,
        "perms": permissions,
        "exp": expire,
        "iat": datetime.now(tz=timezone.utc),
    }
    private_key = get_private_key()
    return jwt.encode(payload, private_key, algorithm=settings.token_algorithm)


def decode_token(token: str) -> dict:
    public_key = get_public_key()
    return jwt.decode(token, public_key, algorithms=[settings.token_algorithm])
