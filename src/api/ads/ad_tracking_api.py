from flask import Blueprint, request, jsonify, current_app
from database.connection import get_collection
from bson import ObjectId
from datetime import datetime

ads_tracking_bp = Blueprint(
    "ads_tracking_bp",
    __name__,
    url_prefix="/api/ads/track"
)


# ---------------------------------------------------------
# Utility: Safe ObjectId conversion
# ---------------------------------------------------------
def safe_oid(val):
    try:
        return ObjectId(val)
    except Exception:
        return None


# ---------------------------------------------------------
# TRACK IMPRESSION
# ---------------------------------------------------------
@ads_tracking_bp.post("/impression")
def track_impression():
    try:
        data = request.get_json(silent=True) or {}

        campaign_id = data.get("campaign_id")
        slot_id = data.get("slot_id")

        if not campaign_id:
            return jsonify({"error": "campaign_id missing"}), 400

        cid = safe_oid(campaign_id)
        if not cid:
            return jsonify({"error": "invalid campaign_id"}), 400

        impressions = get_collection("ads_impressions")
        campaigns = get_collection("campaigns")

        # Track event
        impressions.insert_one({
            "campaign_id": campaign_id,
            "slot_id": slot_id,
            "timestamp": datetime.utcnow(),
            "ip": request.remote_addr,
            "ua": request.headers.get("User-Agent"),
        })

        # Increment counters safely
        campaigns.update_one(
            {"_id": cid},
            {"$inc": {"impressions": 1}}
        )

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        current_app.logger.error(f"[IMPRESSION ERROR] {e}", exc_info=True)
        return jsonify({"error": "server_error"}), 500


# ---------------------------------------------------------
# TRACK CLICK + BILLING (CPC)
# ---------------------------------------------------------
@ads_tracking_bp.post("/click")
def track_click():
    try:
        data = request.get_json(silent=True) or {}

        campaign_id = data.get("campaign_id")
        slot_id = data.get("slot_id")

        if not campaign_id:
            return jsonify({"error": "campaign_id missing"}), 400

        cid = safe_oid(campaign_id)
        if not cid:
            return jsonify({"error": "invalid campaign_id"}), 400

        clicks = get_collection("ads_clicks")
        campaigns = get_collection("campaigns")
        transactions = get_collection("transactions")

        # Log click event
        clicks.insert_one({
            "campaign_id": campaign_id,
            "slot_id": slot_id,
            "timestamp": datetime.utcnow(),
            "ip": request.remote_addr,
            "ua": request.headers.get("User-Agent"),
        })

        # Fetch campaign
        campaign = campaigns.find_one({"_id": cid})
        if not campaign:
            return jsonify({"error": "campaign_not_found"}), 404

        bidding_type = campaign.get("bidding_type", "CPC").upper()
        bid = float(campaign.get("bid_amount", 0) or 0)
        current_budget = float(campaign.get("budget", 0) or 0)

        # Always increment click count
        campaigns.update_one(
            {"_id": cid},
            {"$inc": {"clicks": 1}}
        )

        # -----------------------------
        # CPC Billing Logic
        # -----------------------------
        if bidding_type == "CPC":

            # Budget sufficient?
            if current_budget >= bid:

                # Deduct from campaign budget and increase spend
                campaigns.update_one(
                    {"_id": cid},
                    {"$inc": {"spend": bid, "budget": -bid}}
                )

                # Log a spend transaction (analytics-only)
                transactions.insert_one({
                    "user_id": campaign["user_id"],
                    "campaign_id": campaign_id,
                    "type": "info",
                    "transaction_type": "ad_spend",
                    "amount": bid,
                    "created_at": datetime.utcnow(),
                    "reason": f"campaign:{campaign_id}",
                    "ref_id": f"CPC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "status": "logged"
                })

            else:
                # Budget exhausted → End campaign
                campaigns.update_one(
                    {"_id": cid},
                    {"$set": {"budget": 0, "status": "ended"}}
                )

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        current_app.logger.error(f"[CLICK ERROR] {e}", exc_info=True)
        return jsonify({"error": "server_error"}), 500
