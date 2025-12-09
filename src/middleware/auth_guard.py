"""
Authentication & Authorization Middleware
-----------------------------------------

Provides two decorators:

    @auth_required     → Requires valid Access Token (JWT)
    @admin_required    → Requires user.role == "admin"

Attaches decoded user payload into: g.user
"""

from flask import request, jsonify, g
from functools import wraps

from utils.jwt_helper import verify_jwt
from config.constants import ERR_INVALID_TOKEN, ROLE_ADMIN


# -----------------------------------------------------
# Helper: Extract Bearer token safely
# -----------------------------------------------------
def _get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.removeprefix("Bearer ").strip() or None


# -----------------------------------------------------
# AUTH REQUIRED (Access Token only)
# -----------------------------------------------------
def auth_required(fn):
    """
    Ensures that the client sends a valid JWT *access* token.

    Header format:
        Authorization: Bearer <access_token>
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_bearer_token()
        if not token:
            return jsonify({"error": "Authorization header missing"}), 401

        try:
            payload = verify_jwt(token)

            # Must be an ACCESS token
            if payload.get("type") != "access":
                return jsonify({"error": ERR_INVALID_TOKEN}), 401

            # Attach user payload to flask.g
            g.user = {
                "id": payload.get("sub"),
                "role": payload.get("role", "user"),
            }

        except Exception:
            # Do NOT leak error details in production
            return jsonify({"error": ERR_INVALID_TOKEN}), 401

        return fn(*args, **kwargs)

    return wrapper


# -----------------------------------------------------
# ADMIN REQUIRED (Chain AFTER auth_required)
# -----------------------------------------------------
def admin_required(fn):
    """
    Restrict a route to admins only.

    Usage:

        @app.get("/admin/stats")
        @auth_required
        @admin_required
        def stats():
            return {...}
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):

        user = getattr(g, "user", None)

        # Must be logged in + role = admin
        if not user or str(user.get("role")) != ROLE_ADMIN:
            return jsonify({"error": "Admin access required"}), 403

        return fn(*args, **kwargs)

    return wrapper
