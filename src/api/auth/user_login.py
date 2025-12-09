from flask import Blueprint, request, jsonify, current_app
from database.connection import get_collection
from config.security import verify_password, create_access_token
from utils.request_validator import require_fields
from utils.formatters import format_document
from datetime import datetime

user_login_bp = Blueprint("user_login_bp", __name__)


@user_login_bp.route("/login", methods=["POST"])
def login_user():
    try:
        # Safely read JSON (does not crash on malformed input)
        data = request.get_json(silent=True) or {}

        # Validate input fields
        try:
            require_fields(data, ["email", "password"])
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        # Basic safe production checks
        if not email or "@" not in email:
            return jsonify({"error": "Invalid email"}), 400

        if not password:
            return jsonify({"error": "Password cannot be empty"}), 400

        users = get_collection("users")
        user = users.find_one({"email": email})

        # Authentication failure
        if not user or not verify_password(password, user.get("password", "")):
            return jsonify({"error": "Invalid email or password"}), 401

        # Update last login (UTC)
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )

        # Create JWT access token for user
        token = create_access_token(str(user["_id"]), role="user")

        return jsonify({
            "message": "Login successful",
            "user": format_document(user),
            "access_token": token
        })

    except Exception as e:
        # Log internally, never show technical details to user
        current_app.logger.error(f"[USER LOGIN ERROR] {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
