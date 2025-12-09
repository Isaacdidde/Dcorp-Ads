from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app
)
from database.connection import get_collection
from werkzeug.security import generate_password_hash
from bson import ObjectId
import os
import uuid

settings_bp = Blueprint("user_settings", __name__, template_folder="../../templates/user")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


# ---------------------------------------------------------
# Utility: Validate extension
# ---------------------------------------------------------
def allowed_file(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ---------------------------------------------------------
# Safe ObjectId
# ---------------------------------------------------------
def _safe_oid(v):
    try:
        return ObjectId(v)
    except Exception:
        return v


# ---------------------------------------------------------
# GET Settings Page
# ---------------------------------------------------------
@settings_bp.route("/settings", methods=["GET"])
def settings_page():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    users = get_collection("users")

    try:
        user = users.find_one({"_id": _safe_oid(user_id)})
    except Exception as e:
        current_app.logger.error(f"[SETTINGS] Failed to load user: {e}")
        user = None

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("user_auth.login_page"))

    return render_template("user/settings.html", user=user)


# ---------------------------------------------------------
# UPDATE Settings
# ---------------------------------------------------------
@settings_bp.route("/settings/update", methods=["POST"])
def settings_update():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    users = get_collection("users")

    try:
        user = users.find_one({"_id": _safe_oid(user_id)})
    except Exception as e:
        current_app.logger.error(f"[SETTINGS] Failed loading user: {e}")
        user = None

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("user_settings.settings_page"))

    updated_data = {}

    # -----------------------------------------------------
    # Update: Name
    # -----------------------------------------------------
    new_name = (request.form.get("name") or "").strip()
    if new_name and new_name != user.get("name"):
        updated_data["name"] = new_name

    # -----------------------------------------------------
    # Update: Email
    # -----------------------------------------------------
    new_email = (request.form.get("email") or "").strip()
    if new_email and new_email != user.get("email"):
        updated_data["email"] = new_email

    # -----------------------------------------------------
    # Update: Password
    # -----------------------------------------------------
    new_password = (request.form.get("password") or "").strip()
    if new_password:
        updated_data["password"] = generate_password_hash(new_password)

    # -----------------------------------------------------
    # Update: Profile Picture (Safe Upload)
    # -----------------------------------------------------
    file = request.files.get("profile_image")

    if file and file.filename:
        if allowed_file(file.filename):

            # Correct & safe upload directory
            upload_folder = os.path.join(current_app.root_path, "src", "static", "uploads", "profile")
            upload_folder = os.path.abspath(upload_folder)

            try:
                os.makedirs(upload_folder, exist_ok=True)
            except Exception as e:
                current_app.logger.error(f"[SETTINGS] Could not create upload folder: {e}")

            # Ensure unique and safe file name
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = f"{user_id}_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(upload_folder, filename)

            try:
                file.save(filepath)
                updated_data["profile_pic"] = f"/static/uploads/profile/{filename}"
            except Exception as e:
                current_app.logger.error(f"[SETTINGS] Image upload failed: {e}")
                flash("Failed to upload image. Please try again.", "danger")
                return redirect(url_for("user_settings.settings_page"))

        else:
            flash("Invalid image format. Allowed: JPG, JPEG, PNG, WEBP.", "danger")
            return redirect(url_for("user_settings.settings_page"))

    # -----------------------------------------------------
    # Save Changes to DB
    # -----------------------------------------------------
    if updated_data:
        try:
            users.update_one({"_id": _safe_oid(user_id)}, {"$set": updated_data})
        except Exception as e:
            current_app.logger.error(f"[SETTINGS] DB update failed: {e}")
            flash("Could not update settings. Try again later.", "danger")
            return redirect(url_for("user_settings.settings_page"))

        # Update session if name changed
        if "name" in updated_data:
            session["user_name"] = updated_data["name"]

        flash("Settings updated successfully!", "success")
    else:
        flash("Nothing to update.", "warning")

    return redirect(url_for("user_settings.settings_page"))
