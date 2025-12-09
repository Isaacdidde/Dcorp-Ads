# app.py
from dotenv import load_dotenv
load_dotenv()

import os
import sys

# ============================================================
# FIX: Add src/ and project root to sys.path BEFORE ANY IMPORTS
# ============================================================
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ============================================================
# Imports (now safe)
# ============================================================
from flask import (
    Flask, render_template, request, session,
    redirect, send_from_directory
)
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
import inspect
import importlib
import logging

# App utilities
from utils.timezone import to_ist
from config.settings import settings

# DB
from database.connection import get_collection

# Ads APIs
from api.ads.ad_tracking_api import ads_tracking_bp

from database.connection import get_db
print("Connected DB:", get_db().name)



# ------------------------------------------------------------
# Logger Setup
# ------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dcorp.app")


# ------------------------------------------------------------
# Auto Blueprint Loader
# ------------------------------------------------------------
def register_blueprints_from_module(app, module_path, url_prefix=None, preferred_names=None):
    try:
        module = importlib.import_module(module_path)
    except Exception as e:
        logger.warning(f"[SKIP] Could not import module {module_path}: {e}")
        return []

    registered = []

    # Register only preferred blueprints
    if preferred_names:
        for name in preferred_names:
            bp = getattr(module, name, None)

            if bp and getattr(bp, "__class__", None).__name__ == "Blueprint":
                try:
                    app.register_blueprint(bp, url_prefix=url_prefix)
                    logger.info(f"Registered: {module_path}.{name}")
                    registered.append(name)
                except Exception as err:
                    logger.error(f"Failed to register {module_path}.{name}: {err}")

    # Do NOT auto-register unnamed members.
    # Prevents duplicate blueprint registration.
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

    # ------------------------------------------
    # Security + API Config
    # ------------------------------------------
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DCORP_API_URL"] = settings.DCORP_API_URL

    # CORS
    CORS(app)

    # ------------------------------------------
    # Template Injection: User Info
    # ------------------------------------------
    @app.context_processor
    def inject_user_info():
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
    # Template Injection: IST time
    # ------------------------------------------
    @app.context_processor
    def inject_now():
        return {
            "now": datetime.utcnow,
            "now_ist": lambda: to_ist(datetime.utcnow())
        }

    # ------------------------------------------
    # Static favicon
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
    # Register Admin Panel
    # ------------------------------------------------------
    register_blueprints_from_module(
        app,
        "api.admin.panel",
        url_prefix="/admin",
        preferred_names=["admin_panel_bp"]
    )

    # ------------------------------------------------------
    # Ads Delivery (WINNER PICKING)
    # ------------------------------------------------------
    try:
        from api.ads.routes import ads_slot_api
        app.register_blueprint(ads_slot_api, url_prefix="/api/ads")
        logger.info("Registered ads_slot_api at /api/ads")
    except Exception as e:
        logger.warning(f"Failed to register ads_slot_api: {e}")

    # ------------------------------------------------------
    # ⭐ Impression + Click Tracking (ALREADY has prefix)
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

    for module_path, prefix, names in admin_api_modules:
        register_blueprints_from_module(app, module_path, prefix, names)

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

    for module_path, prefix, names in user_api_modules:
        register_blueprints_from_module(app, module_path, prefix, names)

    # ------------------------------------------------------
    # Public Pages
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
    def handle_404(err):
        if request.path.startswith("/api/"):
            return {"error": "Not Found"}, 404
        return render_template("404.html"), 404

    return app


# ============================================================
# Dev Entry Point
# ============================================================
if __name__ == "__main__":
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=settings.DEBUG
    )
