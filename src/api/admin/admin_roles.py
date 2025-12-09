"""
Admin endpoints for moderating ad creatives and campaigns.
Supports approval, rejection, pausing, activating, and viewing campaigns by slot.
All responses are production-safe and consistent JSON.
"""

from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime
from database.connection import get_collection

# Blueprint registered in app.py
admin_ads_bp = Blueprint("admin_ads_bp", __name__, url_prefix="/api/admin/ads")

# Optional admin authentication middleware
try:
    from middleware.auth import admin_required
except Exception:
    def admin_required(f):
        return f


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def safe_oid(value):
    """Return valid ObjectId or None."""
    try:
        return ObjectId(value)
    except Exception:
        return None


CREATIVES = lambda: get_collection("ad_creatives")
CAMPAIGNS = lambda: get_collection("campaigns")      # FIXED BUG


# =========================================================
# LIST CREATIVES FOR A SLOT (Moderation list)
# =========================================================
@admin_ads_bp.get("/slot/<slot_id>")
@admin_required
def list_creatives_for_slot(slot_id):
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))

        query = {"slot_id": slot_id}
        total = CREATIVES().count_documents(query)

        docs = list(
            CREATIVES()
            .find(query)
            .sort("created_at", -1)
            .skip((page - 1) * per_page)
            .limit(per_page)
        )

        for d in docs:
            d["id"] = str(d.get("_id"))

        return jsonify({"ok": True, "total": total, "creatives": docs}), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN ADS LIST ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500


# =========================================================
# APPROVE CREATIVE
# =========================================================
@admin_ads_bp.post("/creative/<creative_id>/approve")
@admin_required
def approve_creative(creative_id):
    try:
        cid = safe_oid(creative_id)
        if not cid:
            return jsonify({"ok": False, "error": "invalid_id"}), 400

        CREATIVES().update_one(
            {"_id": cid},
            {"$set": {"status": "approved", "updated_at": datetime.utcnow()}}
        )

        return jsonify({"ok": True, "creative_id": creative_id, "status": "approved"}), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN APPROVE ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500


# =========================================================
# REJECT CREATIVE
# =========================================================
@admin_ads_bp.post("/creative/<creative_id>/reject")
@admin_required
def reject_creative(creative_id):
    try:
        cid = safe_oid(creative_id)
        if not cid:
            return jsonify({"ok": False, "error": "invalid_id"}), 400

        CREATIVES().update_one(
            {"_id": cid},
            {"$set": {"status": "rejected", "updated_at": datetime.utcnow()}}
        )

        return jsonify({"ok": True, "creative_id": creative_id, "status": "rejected"}), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN REJECT ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500


# =========================================================
# PAUSE CREATIVE
# =========================================================
@admin_ads_bp.post("/creative/<creative_id>/pause")
@admin_required
def pause_creative(creative_id):
    try:
        cid = safe_oid(creative_id)
        if not cid:
            return jsonify({"ok": False, "error": "invalid_id"}), 400

        CREATIVES().update_one(
            {"_id": cid},
            {"$set": {"status": "paused", "updated_at": datetime.utcnow()}}
        )

        return jsonify({"ok": True, "creative_id": creative_id, "status": "paused"}), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN PAUSE ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500


# =========================================================
# ACTIVATE CREATIVE
# =========================================================
@admin_ads_bp.post("/creative/<creative_id>/activate")
@admin_required
def activate_creative(creative_id):
    try:
        cid = safe_oid(creative_id)
        if not cid:
            return jsonify({"ok": False, "error": "invalid_id"}), 400

        CREATIVES().update_one(
            {"_id": cid},
            {"$set": {"status": "approved", "updated_at": datetime.utcnow()}}
        )

        return jsonify({"ok": True, "creative_id": creative_id, "status": "approved"}), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN ACTIVATE ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500


# =========================================================
# LIST CAMPAIGNS FOR A SLOT (Sorted by bid)
# =========================================================
@admin_ads_bp.get("/campaigns/slot/<slot_id>")
@admin_required
def list_campaigns_for_slot(slot_id):
    try:
        query = {"slot_id": slot_id}

        docs = list(
            CAMPAIGNS()
            .find(query)
            .sort("bid_amount", -1)   # Highest bidders first
        )

        for d in docs:
            d["id"] = str(d["_id"])

        return jsonify({"ok": True, "campaigns": docs}), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN CAMPAIGNS LIST ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500
