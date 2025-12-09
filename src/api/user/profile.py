from flask import Blueprint, render_template, request, redirect, session, flash, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from bson import ObjectId
import os

from database.connection import get_collection

profile_bp = Blueprint("profile", __name__, template_folder="../../templates/user")

# Defining upload folder inside /static for serving
UPLOAD_FOLDER = os.path.join("static", "image", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


# --------------------------------------------------------
# SAFE FILE CHECK
# --------------------------------------------------------
def allowed_file(filename):
    """Ensure the user uploads a clean, valid image extension."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# --------------------------------------------------------
# SAFE OBJECT ID
# --------------------------------------------------------
def _safe_oid(v):
    try:
        return ObjectId(v)
    except Exception:
        return v


# --------------------------------------------------------
# Fetch logged-in user info
# --------------------------------------------------------
def get_user_info():
    user_id = session.get("user_id")
    if not user_id:
        return None

    users = get_collection("users")

    try:
        user = users.find_one({"_id": _safe_oid(user_id)})
    except Exception as e:
        current_app.logger.error(f"[PROFILE] Failed loading user info: {e}")
        return None

    if not user:
        return None

    return {
        "name": user.get("name") or "",
        "email": user.get("email") or "",
        "profile_image": user.get("profile_image") or "/static/uploads/profile.jpg"
    }


# --------------------------------------------------------
# SHOW PROFILE PAGE
# --------------------------------------------------------
@profile_bp.route("/profile", methods=["GET"])
def profile_page():
    user_info = get_user_info()
    if not user_info:
        return redirect("/user/auth/login")
    return render_template("user/profile.html", user_info=user_info)


# --------------------------------------------------------
# UPDATE PROFILE
# --------------------------------------------------------
@profile_bp.route("/profile", methods=["POST"])
def update_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/user/auth/login")

    users = get_collection("users")
    oid = _safe_oid(user_id)

    # ----------------------------------------
    # Safe extraction of form inputs
    # ----------------------------------------
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip()
    password = (request.form.get("password") or "").strip()

    update_data = {}

    if name:
        update_data["name"] = name

    if email:
        update_data["email"] = email

    if password:
        update_data["password"] = generate_password_hash(password)

    # ----------------------------------------
    # Image Upload (safe)
    # ----------------------------------------
    file = request.files.get("profile_image")

    if file and file.filename:
        if allowed_file(file.filename):
            try:
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            except Exception as e:
                current_app.logger.error(f"[PROFILE] Failed to create upload folder: {e}")

            # Secure filename prevents path traversal
            ext = file.filename.rsplit(".", 1)[1].lower()
            filename = secure_filename(f"user_{user_id}.{ext}")

            filepath = os.path.join(UPLOAD_FOLDER, filename)

            try:
                file.save(filepath)
                update_data["profile_image"] = f"/static/image/uploads/{filename}"
            except Exception as e:
                current_app.logger.error(f"[PROFILE] Failed to save profile image: {e}")
                flash("Image upload failed. Try again.", "user_error")
        else:
            flash("Invalid image format. Allowed: JPG, PNG, WEBP.", "user_error")
            return redirect("/user/profile")

    # ----------------------------------------
    # APPLY UPDATE TO DATABASE
    # ----------------------------------------
    if update_data:
        try:
            users.update_one({"_id": oid}, {"$set": update_data})
        except Exception as e:
            current_app.logger.error(f"[PROFILE] DB update failed: {e}")
            flash("Could not update profile. Try again.", "user_error")
            return redirect("/user/profile")

    flash("Profile updated successfully!", "user_success")
    return redirect("/user/profile")
