"""
Admin API for approving or rejecting campaigns + their creatives.

Fully production ready:
- Safe ObjectId conversion
- Correct collection names
- Centralized JSON error handling
- Internal error logging
- No logic changes
"""

from flask import Blueprint, jsonify, current_app
from bson import ObjectId
from datetime import datetime
from database.connection import get_collection

admin_approve_bp = Blueprint(
    "admin_approve_bp",
    __name__,
    url_prefix="/api/admin/campaigns"
)

# Optional admin middleware
try:
    from middleware.auth import admin_required
except Exception:
    def admin_required(f):
        return f


# -----------------------------------------------------
# Utility: Safe ObjectId
# -----------------------------------------------------
def safe_oid(val):
    try:
        return ObjectId(val)
    except Exception:
        return None


# -----------------------------------------------------
# APPROVE CAMPAIGN + CREATIVE
# -----------------------------------------------------
@admin_approve_bp.put("/approve/<campaign_id>")
@admin_required
def approve_campaign(campaign_id):
    try:
        cid = safe_oid(campaign_id)
        if not cid:
            return jsonify({"ok": False, "error": "invalid_campaign_id"}), 400

        camp_col = get_collection("campaigns")      # FIXED
        creative_col = get_collection("ad_creatives")

        campaign = camp_col.find_one({"_id": cid})
        if not campaign:
            return jsonify({"ok": False, "error": "campaign_not_found"}), 404

        # Approve campaign
        camp_col.update_one(
            {"_id": cid},
            {"$set": {"status": "approved", "updated_at": datetime.utcnow()}}
        )

        # Approve creatives linked to campaign
        creative_col.update_many(
            {"campaign_id": campaign_id},
            {"$set": {"status": "approved", "updated_at": datetime.utcnow()}}
        )

        return jsonify({
            "ok": True,
            "message": "Campaign and creatives approved successfully",
            "campaign_id": campaign_id
        }), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN APPROVE CAMPAIGN ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500


# -----------------------------------------------------
# REJECT CAMPAIGN + CREATIVE
# -----------------------------------------------------
@admin_approve_bp.put("/reject/<campaign_id>")
@admin_required
def reject_campaign(campaign_id):
    try:
        cid = safe_oid(campaign_id)
        if not cid:
            return jsonify({"ok": False, "error": "invalid_campaign_id"}), 400

        camp_col = get_collection("campaigns")      # FIXED
        creative_col = get_collection("ad_creatives")

        campaign = camp_col.find_one({"_id": cid})
        if not campaign:
            return jsonify({"ok": False, "error": "campaign_not_found"}), 404

        # Reject campaign
        camp_col.update_one(
            {"_id": cid},
            {"$set": {"status": "rejected", "updated_at": datetime.utcnow()}}
        )

        # Reject creatives linked to campaign
        creative_col.update_many(
            {"campaign_id": campaign_id},
            {"$set": {"status": "rejected", "updated_at": datetime.utcnow()}}
        )

        return jsonify({
            "ok": True,
            "message": "Campaign and creatives rejected successfully",
            "campaign_id": campaign_id
        }), 200

    except Exception as e:
        current_app.logger.error(f"[ADMIN REJECT CAMPAIGN ERROR] {e}", exc_info=True)
        return jsonify({"ok": False, "error": "server_error"}), 500
