# api/analytics/track_event.py
from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime
from ..ads.billing.update_balance import charge_for_event

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

def get_db():
    from database.connection import get_db
    return get_db()

@analytics_bp.route("/track", methods=["GET","POST"])
def track():
    """
    Accept query params or JSON:
      event=impression|click
      campaign_id, creative_id, slot
    This endpoint records the event and calls billing.
    """
    data = request.get_json(silent=True) or request.args
    event = data.get("event")
    campaign_id = data.get("campaign_id")
    creative_id = data.get("creative_id")
    slot = data.get("slot")
    if not event or not campaign_id:
        return jsonify({"error":"missing params"}), 400

    db = get_db()
    rec = {
        "campaign_id": ObjectId(campaign_id),
        "creative_id": ObjectId(creative_id) if creative_id else None,
        "slot": slot,
        "event": event,
        "ip": request.remote_addr,
        "ua": request.headers.get("User-Agent"),
        "ts": datetime.utcnow()
    }
    # Store raw event
    db.ad_events.insert_one(rec)

    # Now charge/bill according to event type and campaign config
    try:
        charge_for_event(db, campaign_id, event, rec)
    except Exception as e:
        # billing errors shouldn't break tracking; log
        current_app = None
        # If you have logging setup:
        # current_app.logger.exception("Billing error")
        print("Billing error:", e)

    return jsonify({"status":"ok"}), 200
