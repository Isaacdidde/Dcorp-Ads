# src/api/admin/admin_ads.py
"""
Admin endpoints for moderating ad creatives and campaigns.
Supports: approve, reject, pause, activate, list by slot, view campaigns by slot.
"""

from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from database.connection import get_collection

# Blueprint: matches app.py registration
admin_ads_bp = Blueprint("admin_ads_bp", __name__, url_prefix="/api/admin/ads")

# Optional admin authentication
try:
    from middleware.auth import admin_required
except Exception:
    def admin_required(f):
        return f


# ------------------------------
# Helpers
# ------------------------------
def safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


CREATIVES = lambda: get_collection("ad_creatives")
CAMPAIGNS = lambda: get_collection("ad_campaigns")


# ============================================================
# LIST CREATIVE ADS FOR A SLOT (Moderation List)
# ============================================================
@admin_ads_bp.get("/slot/<slot_id>")
@admin_required
def list_creatives_for_slot(slot_id):
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

    # Clean IDs
    for d in docs:
        d["id"] = str(d["_id"])

    return jsonify({"ok": True, "total": total, "creatives": docs}), 200


# ============================================================
# APPROVE CREATIVE
# ============================================================
@admin_ads_bp.post("/creative/<creative_id>/approve")
@admin_required
def approve_creative(creative_id):
    cid = safe_oid(creative_id)
    if not cid:
        return jsonify({"ok": False, "error": "Invalid creative ID"}), 400

    CREATIVES().update_one(
        {"_id": cid},
        {
            "$set": {
                "status": "approved",
                "updated_at": datetime.utcnow()
            }
        }
    )

    return jsonify({"ok": True, "creative_id": creative_id, "status": "approved"}), 200


# ============================================================
# REJECT CREATIVE
# ============================================================
@admin_ads_bp.post("/creative/<creative_id>/reject")
@admin_required
def reject_creative(creative_id):
    cid = safe_oid(creative_id)
    if not cid:
        return jsonify({"ok": False, "error": "Invalid creative ID"}), 400

    CREATIVES().update_one(
        {"_id": cid},
        {
            "$set": {
                "status": "rejected",
                "updated_at": datetime.utcnow()
            }
        }
    )

    return jsonify({"ok": True, "creative_id": creative_id, "status": "rejected"}), 200


# ============================================================
# PAUSE CREATIVE
# ============================================================
@admin_ads_bp.post("/creative/<creative_id>/pause")
@admin_required
def pause_creative(creative_id):
    cid = safe_oid(creative_id)
    if not cid:
        return jsonify({"ok": False, "error": "Invalid creative ID"}), 400

    CREATIVES().update_one(
        {"_id": cid},
        {
            "$set": {
                "status": "paused",
                "updated_at": datetime.utcnow()
            }
        }
    )

    return jsonify({"ok": True, "creative_id": creative_id, "status": "paused"}), 200


# ============================================================
# ACTIVATE CREATIVE (Like unpause)
# ============================================================
@admin_ads_bp.post("/creative/<creative_id>/activate")
@admin_required
def activate_creative(creative_id):
    cid = safe_oid(creative_id)
    if not cid:
        return jsonify({"ok": False, "error": "Invalid creative ID"}), 400

    CREATIVES().update_one(
        {"_id": cid},
        {
            "$set": {
                "status": "approved",
                "updated_at": datetime.utcnow()
            }
        }
    )

    return jsonify({"ok": True, "creative_id": creative_id, "status": "approved"}), 200


# ============================================================
# LIST CAMPAIGNS FOR A SLOT (sorted by bid)
# ============================================================
@admin_ads_bp.get("/campaigns/slot/<slot_id>")
@admin_required
def list_campaigns_for_slot(slot_id):
    query = {"slot_id": slot_id}

    docs = list(
        CAMPAIGNS()
        .find(query)
        .sort("bid_amount", -1)  # highest bid first
    )

    for d in docs:
        d["id"] = str(d["_id"])

    return jsonify({"ok": True, "campaigns": docs}), 200
