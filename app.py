# app.py
from dotenv import load_dotenv
load_dotenv()

import os
import sys

# ============================================================
# Ensure project root and src/ are in sys.path BEFORE imports
# ============================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ============================================================
# Imports (safe)
# ============================================================
from flask import (
    Flask, render_template, request, session,
    redirect, send_from_directory
)
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
import importlib
import inspect
import logging

# Utilities
from utils.timezone import to_ist
from config.settings import settings

# Database
from database.connection import get_collection, get_db

# Tracking API
from api.ads.ad_tracking_api import ads_tracking_bp

# Debug print (safe for prod)
print(f"✅ MongoDB Connected: {get_db().name}")

# ------------------------------------------------------------
# Logger
# ------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dcorp.app")


# ------------------------------------------------------------
# Blueprint Loader (NO auto-discovery)
# ------------------------------------------------------------
def register_blueprints_from_module(app, module_path, url_prefix=None, preferred_names=None):
    """
    Only registers explicitly-named blueprints.
    Prevents duplicate blueprint names and accidental imports.
    """
    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        logger.warning(f"[SKIP] Could not import module {module_path}: {e}")
        return []

    registered = []

    if preferred_names:
        for name in preferred_names:
            bp = getattr(module, name, None)

            if not bp:
                continue

            if getattr(bp, "__class__", None).__name__ != "Blueprint":
                continue

            try:
                app.register_blueprint(bp, url_prefix=url_prefix)
                logger.info(f"Registered: {module_path}.{name}")
                registered.append(name)
            except Exception as err:
                logger.error(f"Failed to register {module_path}.{name}: {err}")

    return registered


# ------------------------------------------------------------
# Application Factory
# ------------------------------------------------------------
def create_app():
    app = Flask(
        __name__,
        template_folder="src/templates",
        static_folder="src/static"
    )

    # Security
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DCORP_API_URL"] = settings.DCORP_API_URL

    # CORS
    CORS(app)

    # ------------------------------------------
    # Inject logged-in user into templates
    # ------------------------------------------
    @app.context_processor
    def inject_user():
        uid = session.get("user_id")
        if not uid:
            return {"user_info": None}

        users = get_collection("users")
        try:
            user = users.find_one({"_id": ObjectId(uid)})
        except:
            user = users.find_one({"_id": uid})

        return {"user_info": user}

    # ------------------------------------------
    # Inject IST time into templates
    # ------------------------------------------
    @app.context_processor
    def inject_time():
        return {
            "now": datetime.utcnow,
            "now_ist": lambda: to_ist(datetime.utcnow())
        }

    # ------------------------------------------
    # Favicon
    # ------------------------------------------
    @app.route("/favicon.ico")
    def favicon():
        try:
            return send_from_directory(
                app.static_folder,
                "favicon.ico",
                mimetype="image/x-icon"
            )
        except Exception:
            return "", 204

    # ------------------------------------------------------
    # Admin Panel
    # ------------------------------------------------------
    register_blueprints_from_module(
        app,
        "api.admin.panel",
        url_prefix="/admin",
        preferred_names=["admin_panel_bp"]
    )

    # ------------------------------------------------------
    # Ads Delivery (Winner Picking)
    # ------------------------------------------------------
    try:
        from api.ads.routes import ads_slot_api
        app.register_blueprint(ads_slot_api, url_prefix="/api/ads")
        logger.info("Registered ads_slot_api at /api/ads")
    except Exception as e:
        logger.warning(f"Failed to register ads_slot_api: {e}")

    # ------------------------------------------------------
    # Impression + Click Tracking
    # (Prefix already inside the blueprint)
    # ------------------------------------------------------
    app.register_blueprint(ads_tracking_bp)
    logger.info("Registered ads_tracking_bp at /api/ads/track")

    # ------------------------------------------------------
    # Admin API Blueprints
    # ------------------------------------------------------
    admin_api_modules = [
        ("api.auth.login", None, ["auth_login_bp"]),
        ("api.auth.register", None, ["auth_register_bp"]),
        ("api.auth.refresh_token", None, ["auth_refresh_bp"]),
        ("api.auth.user_login", "/auth", ["user_login_bp"]),

        ("api.products.product_controller", "/api/products", ["product_bp"]),
        ("api.products.get_products", "/api/products", ["get_products_bp"]),
        ("api.products.register_product", "/api/products", ["register_product_bp"]),

        ("api.admin.admin_ads", "/api/admin/ads", ["admin_ads_bp"]),
        ("api.advertisers.advertiser_profile", "/api/advertisers", ["advertiser_profile_bp"]),
        ("api.advertisers.wallet", "/api/advertisers", ["wallet_bp"]),

        ("api.analytics.stats_overview", "/api/analytics", ["analytics_stats_bp"]),
        ("api.analytics.product_analytics", "/api/analytics", ["product_analytics_bp"]),

        ("api.billing.billing_controller", "/api/billing", ["billing_bp"]),
        ("api.billing.transaction_logs", "/api/billing", ["transaction_logs_bp"]),
    ]

    for module, prefix, names in admin_api_modules:
        register_blueprints_from_module(app, module, prefix, names)

    # ------------------------------------------------------
    # User API Blueprints
    # ------------------------------------------------------
    user_api_modules = [
        ("api.user.auth", "/user/auth", ["user_auth_bp"]),
        ("api.user.profile", "/user", ["profile_bp"]),
        ("api.user.dashboard", "/user", ["user_dashboard_bp"]),

        ("api.user.campaign", None, ["campaign_bp"]),
        ("api.user.bidding", "/user", ["bidding_bp"]),
        ("api.user.placement", "/user", ["placement_bp"]),
        ("api.user.wallet", "/user", ["wallet_bp"]),
        ("api.user.billing", "/user", ["billing_bp"]),
        ("api.user.settings", "/user", ["settings_bp"]),
    ]

    for module, prefix, names in user_api_modules:
        register_blueprints_from_module(app, module, prefix, names)

    # ------------------------------------------------------
    # Public Routes
    # ------------------------------------------------------
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/pricing")
    def pricing():
        return render_template("pricing.html")

    @app.route("/features")
    def features():
        return render_template("features.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/")

    # ------------------------------------------------------
    # 404 Handler
    # ------------------------------------------------------
    @app.errorhandler(404)
    def not_found(err):
        if request.path.startswith("/api/"):
            return {"error": "Not Found"}, 404
        return render_template("404.html"), 404

    return app


# ============================================================
# Development Entry Point
# ============================================================
if __name__ == "__main__":
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=settings.DEBUG
    )
