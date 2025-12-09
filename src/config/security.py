"""
Security utilities used across the DCorp backend.

Handles:
- Password hashing & verification
- JWT creation (access & refresh tokens)
- JWT verification
- Token blacklist protection (optional future use)
"""

import os
import time
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from config.settings import settings
from config.constants import (
    ERR_INVALID_TOKEN,
    ERR_UNAUTHORIZED,
    ROLE_USER,
    ROLE_ADMIN,
)

# ---------------------------------------------------------------------
# PASSWORD HASHING
# ---------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password using Werkzeug (PBKDF2)."""
    return generate_password_hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify user-entered password against stored hashed password."""
    try:
        return check_password_hash(hashed, plain)
    except Exception:
        return False


# ---------------------------------------------------------------------
# JWT CONFIG
# ---------------------------------------------------------------------
JWT_SECRET = settings.JWT_SECRET_KEY
JWT_ALGO = "HS256"

ACCESS_TOKEN_EXP_MIN = settings.JWT_ACCESS_EXPIRE_MINUTES        # e.g., 30 min
REFRESH_TOKEN_EXP_MIN = settings.JWT_REFRESH_EXPIRE_MINUTES      # e.g., 30 days


# ---------------------------------------------------------------------
# JWT CREATION HELPERS
# ---------------------------------------------------------------------

def _generate_token(user_id: str, role: str, expires_in_min: int, token_type: str):
    """Internal function responsible for building JWT payload."""

    now = datetime.utcnow()
    exp = now + timedelta(minutes=expires_in_min)

    payload = {
        "sub": user_id,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),   # issued at
        "exp": int(exp.timestamp()),   # expiration timestamp
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

    # PyJWT returns bytes in older versions—normalize
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token


def create_access_token(user_id: str, role: str = ROLE_USER) -> str:
    """Create short-lived access token."""
    return _generate_token(
        user_id=user_id,
        role=role,
        expires_in_min=ACCESS_TOKEN_EXP_MIN,
        token_type="access"
    )


def create_refresh_token(user_id: str, role: str = ROLE_USER) -> str:
    """Create long-lived refresh token."""
    return _generate_token(
        user_id=user_id,
        role=role,
        expires_in_min=REFRESH_TOKEN_EXP_MIN,
        token_type="refresh"
    )


# ---------------------------------------------------------------------
# TOKEN VERIFICATION
# ---------------------------------------------------------------------

def verify_jwt_token(token: str):
    """
    Verify JWT signature and expiry.
    Returns decoded payload or raises Exception.
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception(ERR_INVALID_TOKEN)


# ---------------------------------------------------------------------
# ROLE CHECK HELPERS
# ---------------------------------------------------------------------

def is_admin(decoded_token) -> bool:
    """Check if token contains admin privileges."""
    return decoded_token.get("role") == ROLE_ADMIN


def is_user(decoded_token) -> bool:
    """Check if token is normal user."""
    return decoded_token.get("role") == ROLE_USER


# ---------------------------------------------------------------------
# OPTIONAL: TOKEN BLACKLIST (future-proof)
# Uncomment and implement when you add logout-invalidate logic.
# ---------------------------------------------------------------------
# from database.connection import get_collection
#
# def blacklist_token(jti):
#     get_collection("jwt_blacklist").insert_one({
#         "jti": jti,
#         "blacklisted_at": datetime.utcnow()
#     })
#
# def is_token_blacklisted(jti):
#     return get_collection("jwt_blacklist").find_one({"jti": jti}) is not None
