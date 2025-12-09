# src/api/advertisers/campaign_list.py
from flask import Blueprint, jsonify, request
from database.connection import get_collection
from bson import ObjectId

campaign_list_bp = Blueprint(
    "advertiser_campaign_list",
    __name__,
    url_prefix="/api/advertisers"
)

@campaign_list_bp.route("/campaigns", methods=["GET"])
def list_campaigns():
    advertiser_id = request.args.get("advertiser_id")
    try:
        oid = ObjectId(advertiser_id)
    except:
        return jsonify({"ok": False, "error": "invalid advertiser_id"}), 400

    campaigns = list(
        get_collection("ad_campaigns")
        .find({"advertiser_id": oid})
        .sort("created_at", -1)
    )

    for c in campaigns:
        c["_id"] = str(c["_id"])
        c["advertiser_id"] = str(c["advertiser_id"])

    return jsonify({"ok": True, "campaigns": campaigns})
