from flask import Blueprint, request, render_template, redirect, session, flash, url_for, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import get_collection
from datetime import datetime
from utils.timezone import IST
from urllib.parse import urlparse

user_auth_bp = Blueprint("user_auth", __name__, template_folder="../../templates/user")


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def _valid_email(email: str) -> bool:
    """Basic sanity check for email format."""
    if not email or "@" not in email or "." not in email:
        return False
    return True


def _valid_password(password: str) -> bool:
    """Production-safe rule: minimum 6 characters."""
    return password and len(password) >= 6


def _safe_redirect(target: str):
    """
    Prevent open redirect attacks.
    Only allow internal URLs.
    """
    if not target:
        return url_for("user_dashboard_bp.dashboard")

    parsed = urlparse(target)
    if parsed.netloc:  # External domain → block
        return url_for("user_dashboard_bp.dashboard")

    return target


# ===================================================================
# SHOW LOGIN PAGE
# ===================================================================
@user_auth_bp.route("/login", methods=["GET"])
def login_page():
    # Clear admin session to avoid collision
    session.pop("admin_id", None)
    return render_template("user/login.html")


# ===================================================================
# HANDLE LOGIN SUBMISSION
# ===================================================================
@user_auth_bp.route("/login", methods=["POST"])
def login_submit():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # Input validation
    if not _valid_email(email):
        flash("Please enter a valid email address.", "user_error")
        return redirect(url_for("user_auth.login_page"))

    if not password:
        flash("Please enter your password.", "user_error")
        return redirect(url_for("user_auth.login_page"))

    users = get_collection("users")
    user = users.find_one({"email": email})

    if not user:
        flash("No account found with this email.", "user_error")
        return redirect(url_for("user_auth.login_page"))

    db_password = user.get("password")
    if not db_password:
        flash("Account has no password. Please reset or register again.", "user_error")
        return redirect(url_for("user_auth.login_page"))

    if not check_password_hash(db_password, password):
        flash("Incorrect password.", "user_error")
        return redirect(url_for("user_auth.login_page"))

    # --------------------------------------------------------
    # Update last login timestamp (IST)
    # --------------------------------------------------------
    users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(IST)}}
    )

    # Login success
    session.clear()
    session["user_id"] = str(user["_id"])
    session["user_name"] = user.get("name")

    # Optional: log the login event for audit
    current_app.logger.info(f"User logged in: {email}")

    flash("Login successful!", "user_success")
    return redirect("/user/dashboard")


# ===================================================================
# SHOW REGISTER PAGE
# ===================================================================
@user_auth_bp.route("/register", methods=["GET"])
def register_page():
    session.pop("admin_id", None)
    return render_template("user/register.html")


# ===================================================================
# HANDLE REGISTER SUBMISSION
# ===================================================================
@user_auth_bp.route("/register", methods=["POST"])
def register_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password")

    # ---------------------------------------
    # VALIDATION
    # ---------------------------------------
    if not name:
        flash("Name is required.", "user_error")
        return redirect(url_for("user_auth.register_page"))

    if not _valid_email(email):
        flash("Please enter a valid email address.", "user_error")
        return redirect(url_for("user_auth.register_page"))

    if not _valid_password(password):
        flash("Password must be at least 6 characters long.", "user_error")
        return redirect(url_for("user_auth.register_page"))

    users = get_collection("users")

    # Prevent duplicate registration
    if users.find_one({"email": email}):
        flash("This email already exists. Please login instead.", "user_error")
        return redirect(url_for("user_auth.register_page"))

    # --------------------------------------------------------
    # Insert user document
    # --------------------------------------------------------
    new_user = {
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "profile_image": None,
        "wallet_balance": 0.0,
        "created_at": datetime.utcnow(),
        "last_login": None
    }

    result = users.insert_one(new_user)

    session.clear()
    session["user_id"] = str(result.inserted_id)
    session["user_name"] = name

    current_app.logger.info(f"New user registered: {email}")

    flash("Account created successfully!", "user_success")
    return redirect("/user/dashboard")


# ===================================================================
# LOGOUT USER
# ===================================================================
@user_auth_bp.route("/logout_user")
def logout_user():
    session.clear()
    return redirect("/")
