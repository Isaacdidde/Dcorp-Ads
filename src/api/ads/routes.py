from flask import Blueprint, jsonify, current_app, request
from services.ads.bidding_engine import get_winning_ad

# Mounted at /api/ads in app.py
ads_slot_api = Blueprint("ads_slot_api", __name__)


# =====================================================================
# AD DELIVERY ENDPOINT (CRITICAL — ZERO BILLING HERE)
# =====================================================================
@ads_slot_api.route("/slot/<slot_id>", methods=["GET"])
def get_ad_slot(slot_id):
    """
    Returns the winning ad for the requested slot.
    Bidding logic is handled by bidding_engine.
    Billing happens ONLY in tracking endpoints (/api/ads/track).
    """
    try:
        # Sanitize slot_id (just in case)
        slot_id = (slot_id or "").strip()

        if not slot_id:
            return jsonify({
                "ad": None,
                "error": "slot_id is required"
            }), 400

        # Execute bidding engine
        ad = get_winning_ad(slot_id)

        # No ads available for this slot
        if not ad:
            return jsonify({
                "ad": None,
                "message": "No eligible ads for this slot."
            }), 200

        # Successful ad response
        return jsonify({"ad": ad}), 200

    except Exception as e:
        # Log full traceback internally
        current_app.logger.error(
            f"[AD SLOT ERROR] slot_id={slot_id}, error={e}",
            exc_info=True
        )

        # Do NOT expose internal error details to client
        return jsonify({
            "ad": None,
            "error": "internal_server_error"
        }), 500
