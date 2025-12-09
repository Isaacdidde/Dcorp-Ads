from flask import Blueprint, request, jsonify, redirect, flash, url_for, session, current_app
from database.connection import get_collection
from config.security import verify_password, create_access_token, create_refresh_token
from utils.request_validator import require_fields
from utils.formatters import format_document
from datetime import datetime

auth_login_bp = Blueprint("auth_login_bp", __name__)


@auth_login_bp.route("/login", methods=["POST"])
def login():
    try:
        # Accept JSON or form-encoded requests safely
        json_data = request.get_json(silent=True) or {}
        form_data = request.form.to_dict() if request.form else {}
        data = json_data if json_data else form_data

        # Validate expected fields
        try:
            require_fields(data, ["email", "password"])
        except Exception as e:
            # HTML UI → redirect with error
            if form_data:
                flash("Email and password are required.", "danger")
                return redirect(url_for("admin_panel.login"))

            # API JSON → 400 Bad Request
            return jsonify({"error": str(e)}), 400

        admins = get_collection("admins")

        # Fetch admin safely
        try:
            admin = admins.find_one({"email": data["email"]})
        except Exception as e:
            current_app.logger.error(f"[AUTH] DB lookup failure: {e}")
            admin = None

        # Invalid credentials
        if not admin or not verify_password(data["password"], admin.get("password", "")):

            # HTML Admin Panel request
            if form_data:
                flash("Invalid email or password", "danger")
                return redirect(url_for("admin_panel.login"))

            # API JSON request
            return jsonify({"error": "Invalid email or password"}), 401

        # Update last login timestamp safely
        try:
            admins.update_one(
                {"_id": admin["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception as e:
            current_app.logger.error(f"[AUTH] Failed to update last_login: {e}")

        # Generate tokens
        role = admin.get("role", "admin")

        try:
            access_token = create_access_token(str(admin["_id"]), role=role)
            refresh_token = create_refresh_token(str(admin["_id"]), role=role)
        except Exception as e:
            current_app.logger.error(f"[AUTH] Token generation failed: {e}")
            return jsonify({"error": "Authorization failure"}), 500

        # -------------------------------------------
        # HTML Login (Admin Panel)
        # -------------------------------------------
        if form_data:
            session["admin_id"] = str(admin["_id"])
            session["admin_role"] = role
            session["admin_email"] = admin.get("email", "")
            session["access_token"] = access_token

            return redirect(url_for("admin_panel.index"))

        # -------------------------------------------
        # JSON API Response
        # -------------------------------------------
        return jsonify({
            "admin": format_document(admin),
            "access_token": access_token,
            "refresh_token": refresh_token
        })

    except Exception as e:
        # Log error for debugging, return safe response to user
        current_app.logger.error(f"[AUTH LOGIN ERROR] {e}", exc_info=True)

        # Do NOT expose internal errors to the user in production
        if request.form:
            flash("An unexpected error occurred. Try again.", "danger")
            return redirect(url_for("admin_panel.login"))

        return jsonify({"error": "Server error"}), 500
