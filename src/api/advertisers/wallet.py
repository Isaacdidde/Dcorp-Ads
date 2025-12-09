# src/api/advertisers/wallet.py
from flask import Blueprint, request, jsonify
from database.connection import get_collection
from datetime import datetime
from bson import ObjectId

wallet_bp = Blueprint("advertiser_wallet", __name__, url_prefix="/api/advertisers")

@wallet_bp.route("/wallet/balance/<aid>", methods=["GET"])
def get_balance(aid):
    try:
        oid = ObjectId(aid)
    except:
        return jsonify({"ok": False, "error": "Invalid advertiser ID"}), 400

    tx = list(get_collection("advertiser_wallet").find({"advertiser_id": oid}))

    balance = sum(t.get("amount", 0) for t in tx)

    return jsonify({"ok": True, "balance": balance})
