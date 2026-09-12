import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials


password_hash = PasswordHash.recommended()
oauth2_scheme = HTTPBearer()
def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is not set."
        )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is not set."
        )

    return jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
    )

def get_user_id_from_token(token: str) -> int:
    payload = decode_access_token(token)

    user_id = payload.get("sub")

    if user_id is None:
        raise ValueError("Invalid token")

    return int(user_id)
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> int:
    try:
        return get_user_id_from_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")