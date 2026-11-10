"""Prototype password hashing and in-memory bearer-token authentication."""
import hashlib
import hmac
import secrets

from fastapi import Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User

# Token sessions vanish on server restart; use a real session store for production.
TOKENS: dict[str, int] = {}
ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        digest = bytes.fromhex(digest_hex)
        check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
        return hmac.compare_digest(digest, check)
    except (ValueError, TypeError):
        return False


def issue_token(user: User) -> str:
    token = secrets.token_hex(16)
    TOKENS[token] = user.id
    return token


def get_current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = TOKENS.get(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User no longer exists")
        session.expunge(user)
        return user


def require_faculty(user: User):
    if user.role != "faculty":
        raise HTTPException(status_code=403, detail="Faculty access required")
