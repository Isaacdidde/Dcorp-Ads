# src/api/advertisers/advertiser_profile.py
from flask import Blueprint, request, jsonify
from database.connection import get_collection
from bson import ObjectId

advertiser_profile_bp = Blueprint(
    "advertiser_profile",
    __name__,
    url_prefix="/api/advertisers"
)

@advertiser_profile_bp.route("/profile/<aid>", methods=["GET"])
def get_profile(aid):
    try:
        oid = ObjectId(aid)
    except:
        return jsonify({"ok": False, "error": "Invalid advertiser ID"}), 400

    advertiser = get_collection("advertisers").find_one({"_id": oid})
    if not advertiser:
        return jsonify({"ok": False, "error": "Not found"}), 404

    advertiser["_id"] = str(advertiser["_id"])
    return jsonify({"ok": True, "profile": advertiser})
