"""
JWT Helper Utilities

This module provides:
- create_jwt()
- verify_jwt()
- decode_jwt()
- create_access_token()
- create_refresh_token()

It complements config/security.py and keeps token creation/validation clean.
"""

import jwt
from datetime import datetime, timedelta
from config.settings import settings


# -----------------------------------------------------
# CREATE GENERIC JWT
# -----------------------------------------------------
def create_jwt(payload: dict, expires_in: int):
    """
    Create a JWT with given payload and expiration time (seconds).
    """
    payload = payload.copy()
    payload["exp"] = datetime.utcnow() + timedelta(seconds=expires_in)
    payload["iat"] = datetime.utcnow()

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


# -----------------------------------------------------
# VERIFY JWT (ACCESS OR REFRESH)
# -----------------------------------------------------
def verify_jwt(token: str):
    """
    Verify and decode a JWT.
    Returns payload dict if valid.
    Raises jwt exceptions if invalid.
    """
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


# -----------------------------------------------------
# CREATE ACCESS TOKEN
# -----------------------------------------------------
def create_access_token(user_id: str, role: str = "user"):
    """
    Access Tokens:
    - short-lived
    - used for API authorization
    """
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access"
    }
    return create_jwt(payload, settings.JWT_ACCESS_EXPIRES)


# -----------------------------------------------------
# CREATE REFRESH TOKEN
# -----------------------------------------------------
def create_refresh_token(user_id: str, role: str = "user"):
    """
    Refresh Tokens:
    - long-lived
    - only used for generating new access tokens
    """
    payload = {
        "sub": user_id,
        "role": role,
        "type": "refresh"
    }
    return create_jwt(payload, settings.JWT_REFRESH_EXPIRES)


# -----------------------------------------------------
# DECODE WITHOUT VERIFYING SIGNATURE (DEBUG USE)
# -----------------------------------------------------
def decode_jwt(token: str):
    """
    Decode JWT without verifying signature.
    Useful for debugging but DO NOT use for authorization.
    """
    return jwt.decode(token, options={"verify_signature": False})
