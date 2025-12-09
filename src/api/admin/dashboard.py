"""
Admin dashboard controller:
- Renders the admin analytics dashboard page
- Serves dashboard JSON metrics for charts/widgets
"""

from flask import Blueprint, jsonify, render_template, current_app
from bson import ObjectId
from datetime import datetime

# DB helpers
from database.connection import get_collection
from config.constants import ERR_INVALID_REQUEST

# Campaigns / Creatives / Products (internal DB-layer)
from database.models.campaign_model import get_all_campaigns
from database.models.ad_model import get_all_ads
from database.models.product_model import get_all_products

# Wallet summary
from database.models.advertiser_model import get_total_wallet_balance


admin_dashboard_bp = Blueprint(
    "admin_dashboard_bp",
    __name__,
    url_prefix="/api/admin"
)


# =====================================================================
# ADMIN DASHBOARD (HTML PAGE)
# =====================================================================
@admin_dashboard_bp.get("/dashboard")
def dashboard_page():
    """
    Returns the admin dashboard UI.
    Gathers analytics from ads, campaigns, users, products, and wallet.
    """

    try:
        # ------------------ REAL Ad Tracking ------------------
        impressions = get_collection("ads_impressions").count_documents({})
        clicks = get_collection("ads_clicks").count_documents({})
        ctr = (clicks / impressions * 100) if impressions > 0 else 0

        # ------------------ Users & Roles ------------------
        users_col = get_collection("users")
        total_users = users_col.count_documents({})
        advertisers = list(users_col.find({"role": "user"}))
        admins = list(users_col.find({"role": "admin"}))

        # ------------------ Campaigns ------------------
        campaigns = get_all_campaigns()
        pending_campaigns = len([c for c in campaigns if c.get("status") == "pending"])

        # ------------------ Creatives ------------------
        creatives_col = get_collection("ad_creatives")
        creatives = list(creatives_col.find({}))
        pending_creatives = len([c for c in creatives if c.get("status") == "pending"])

        # ------------------ Products ------------------
        products = get_all_products()

        # ------------------ Wallet Aggregation ------------------
        wallet_total = get_total_wallet_balance()

        # ------------------ FINAL RESULT ------------------
        stats = {
            "total_users": total_users,
            "total_advertisers": len(advertisers),
            "total_admins": len(admins),

            "total_campaigns": len(campaigns),
            "pending_campaigns": pending_campaigns,

            "total_creatives": len(creatives),
            "pending_creatives": pending_creatives,
            "total_ads": len(get_all_ads()),

            "total_products": len(products),

            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 2),

            "total_wallet_balance": wallet_total,
        }

        return render_template("admin/dashboard.html", stats=stats, products=products)

    except Exception as e:
        current_app.logger.error(f"[ADMIN DASHBOARD ERROR] {e}")
        # Return blank dashboard but do not crash production
        return render_template("admin/dashboard.html", stats={}, products=[])


# =====================================================================
# JSON API: Returns Dashboard Data for Charts (AJAX)
# =====================================================================
@admin_dashboard_bp.get("/dashboard-data")
def dashboard_api():
    """
    Lightweight JSON API used by charts/widgets inside admin dashboard.
    """

    try:
        # ---------- Impressions & Clicks ----------
        impressions = get_collection("ads_impressions").count_documents({})
        clicks = get_collection("ads_clicks").count_documents({})
        ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0

        # ---------- Users ----------
        users_col = get_collection("users")
        total_users = users_col.count_documents({})
        total_advertisers = users_col.count_documents({"role": "user"})
        total_admins = users_col.count_documents({"role": "admin"})

        # ---------- Campaigns ----------
        campaigns = get_all_campaigns()
        pending_campaigns = len([c for c in campaigns if c.get("status") == "pending"])

        # ---------- Creatives ----------
        creatives = list(get_collection("ad_creatives").find())
        pending_creatives = len([c for c in creatives if c.get("status") == "pending"])

        return jsonify({
            "impressions": impressions,
            "clicks": clicks,
            "ctr": ctr,

            "total_users": total_users,
            "total_advertisers": total_advertisers,
            "total_admins": total_admins,

            "total_campaigns": len(campaigns),
            "pending_campaigns": pending_campaigns,

            "total_creatives": len(creatives),
            "pending_creatives": pending_creatives,
        }), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN DASHBOARD API ERROR] {e}")
        return jsonify({"error": ERR_INVALID_REQUEST}), 500
