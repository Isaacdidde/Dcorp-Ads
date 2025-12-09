from flask import Blueprint, request, jsonify, current_app
from config.security import verify_jwt_token, create_access_token
from utils.request_validator import require_fields

auth_refresh_bp = Blueprint("auth_refresh_bp", __name__)


@auth_refresh_bp.route("/refresh", methods=["POST"])
def refresh_token():
    try:
        # Gracefully handle missing/invalid JSON
        data = request.get_json(silent=True) or {}

        try:
            require_fields(data, ["refresh_token"])
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        refresh_token = data.get("refresh_token")

        # -------------------------------------------------------
        # Verify Refresh Token
        # -------------------------------------------------------
        try:
            decoded = verify_jwt_token(refresh_token)
        except Exception as e:
            current_app.logger.warning(f"[JWT REFRESH] Verification failed: {e}")
            return jsonify({"error": "Invalid or expired token"}), 401

        # -------------------------------------------------------
        # Must be refresh token
        # -------------------------------------------------------
        if decoded.get("type") != "refresh":
            current_app.logger.warning("[JWT REFRESH] Wrong token type used")
            return jsonify({"error": "Invalid token type"}), 401

        # -------------------------------------------------------
        # Extract user + role
        # -------------------------------------------------------
        user_id = decoded.get("sub")
        role = decoded.get("role", "user")

        if not user_id:
            current_app.logger.error("[JWT REFRESH] Missing subject in token")
            return jsonify({"error": "Invalid token"}), 401

        # -------------------------------------------------------
        # Generate new access token
        # -------------------------------------------------------
        try:
            new_access_token = create_access_token(user_id, role=role)
        except Exception as e:
            current_app.logger.error(f"[JWT REFRESH] Failed to create access token: {e}")
            return jsonify({"error": "Token generation failed"}), 500

        return jsonify({
            "access_token": new_access_token,
            "message": "Access token refreshed"
        })

    except Exception as e:
        # Never expose internal error
        current_app.logger.error(f"[JWT REFRESH UNKNOWN ERROR] {e}", exc_info=True)
        return jsonify({"error": "Server error"}), 500
