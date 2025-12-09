from flask import Blueprint, request, jsonify, current_app
from database.connection import get_collection
from config.security import hash_password
from utils.request_validator import require_fields
from utils.formatters import format_document
from datetime import datetime

auth_register_bp = Blueprint("auth_register_bp", __name__)


@auth_register_bp.route("/register", methods=["POST"])
def register():
    try:
        # Safe JSON input (never crashes on bad JSON)
        data = request.get_json(silent=True) or {}

        # Validate required fields
        try:
            require_fields(data, ["name", "email", "password"])
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        # Basic production-grade sanitization
        if not name:
            return jsonify({"error": "Name cannot be empty"}), 400

        if "@" not in email:
            return jsonify({"error": "Invalid email"}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        users = get_collection("users")

        # ---------------------------------------------------
        # Duplicate Email Check
        # ---------------------------------------------------
        existing = users.find_one({"email": email})
        if existing:
            return jsonify({"error": "Email already registered"}), 400

        # ---------------------------------------------------
        # Create User Document
        # ---------------------------------------------------
        new_user = {
            "name": name,
            "email": email,
            "password": hash_password(password),
            "role": "user",  # fixed role

            # Production-safe default fields
            "created_at": datetime.utcnow(),
            "last_login": None,
            "wallet": 0.0,  # consistent numeric wallet
        }

        inserted = users.insert_one(new_user)
        saved_user = users.find_one({"_id": inserted.inserted_id})

        return jsonify({
            "message": "Registration successful",
            "user": format_document(saved_user)
        }), 201

    except Exception as e:
        # INTERNAL ERROR → Log it, do NOT expose it
        current_app.logger.error(f"[REGISTER ERROR] {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
