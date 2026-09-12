import hmac
import hashlib
import json
import base64
import secrets
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "spend-analyzer-super-secret-key-change-in-prod-2026")
TOKEN_EXPIRE_HOURS = 24 * 7  # 7 days


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return pw_hash, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    pw_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(pw_hash, expected_hash)


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data.encode('utf-8'))


def create_access_token(user_id: str, email: str, username: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "username": username,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }

    header_b64 = _b64_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload).encode('utf-8'))
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        f"{header_b64}.{payload_b64}".encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            f"{header_b64}.{payload_b64}".encode('utf-8'),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(_b64_encode(expected_sig), sig_b64):
            return None

        payload = json.loads(_b64_decode(payload_b64).decode('utf-8'))
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            return None

        return payload
    except Exception:
        return None


@dataclass
class SessionContext:
    user: Optional[User] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    is_transient: bool = False
    is_authenticated: bool = False


async def get_session_context(
    authorization: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None),
    x_transient_mode: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> SessionContext:
    context = SessionContext()

    # 1. Check for Bearer token in Authorization header
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            res = await db.execute(select(User).where(User.id == payload["sub"]))
            user = res.scalar_one_or_none()
            if user:
                context.user = user
                context.user_id = user.id
                context.is_authenticated = True

    # 2. Check for transient/session header
    is_transient = (x_transient_mode == "true") or (x_transient_mode == "1")
    context.is_transient = is_transient

    if x_session_id and x_session_id.strip():
        context.session_id = x_session_id.strip()
    elif is_transient:
        # Generate ephemeral session id if marked transient but none provided
        context.session_id = secrets.token_hex(16)

    return context


async def get_required_user(
    context: SessionContext = Depends(get_session_context)
) -> User:
    if not context.is_authenticated or not context.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return context.user
