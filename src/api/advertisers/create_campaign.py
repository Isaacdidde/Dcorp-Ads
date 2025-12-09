# src/api/advertisers/create_campaign.py
from flask import Blueprint, request, jsonify
from database.connection import get_collection
from datetime import datetime
from bson import ObjectId
from .utils import safe_oid, get_body

create_advertiser_campaign_bp = Blueprint(
    "create_advertiser_campaign",
    __name__,
    url_prefix="/api/advertisers"
)

@create_advertiser_campaign_bp.route("/campaign", methods=["POST"])
def create_campaign():
    body = get_body(request)

    advertiser_id = safe_oid(body.get("advertiser_id"))
    if not advertiser_id:
        return jsonify({"ok": False, "error": "Invalid advertiser_id"}), 400

    name = body.get("name")
    if not name:
        return jsonify({"ok": False, "error": "Campaign name required"}), 400

    slot_id = body.get("slot_id")
    if not slot_id:
        return jsonify({"ok": False, "error": "slot_id is required"}), 400

    bid_amount = float(body.get("bid_amount", 0))
    bidding_type = body.get("bidding_type", "CPC")
    total_budget = float(body.get("total_budget", 0))
    daily_budget = float(body.get("daily_budget", 0))

    doc = {
        "advertiser_id": advertiser_id,
        "name": name,
        "slot_id": slot_id,
        "bid_amount": bid_amount,
        "bidding_type": bidding_type,
        "daily_budget": daily_budget,
        "total_budget": total_budget,
        "remaining_budget": total_budget,
        "status": "pending",        # admin must approve
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    res = get_collection("ad_campaigns").insert_one(doc)
    return jsonify({
        "ok": True,
        "campaign_id": str(res.inserted_id)
    }), 201
