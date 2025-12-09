# src/api/user/bidding.py
from flask import Blueprint, request, render_template, redirect, session, flash, url_for
from database.connection import get_collection
import datetime

bidding_bp = Blueprint("bidding", __name__, template_folder="../../templates/user")

# Show bid settings page
@bidding_bp.route("/bidding/<cid>", methods=["GET"])
def bid_page(cid):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    # fetch campaign to show title
    campaigns_col = get_collection("campaigns")
    campaign = campaigns_col.find_one({"_id": cid}) or campaigns_col.find_one({"_id": __import__("bson").ObjectId(cid)})
    # allow fallback; if not found show simple message
    if campaign:
        # convert _id to string for template
        campaign["_id"] = str(campaign.get("_id"))
    return render_template("user/bidding.html", campaign=campaign)

# Save bid (POST)
@bidding_bp.route("/bidding/<cid>", methods=["POST"])
def save_bid(cid):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    bid_type = request.form.get("bid_type")  # "cpc" or "cpm"
    amount = request.form.get("amount", "0").strip()
    daily_limit = request.form.get("daily_limit", "0").strip()

    try:
        amount = float(amount)
    except Exception:
        amount = 0.0
    try:
        daily_limit = float(daily_limit)
    except Exception:
        daily_limit = 0.0

    bids_col = get_collection("bids")
    new_bid = {
        "campaign_id": cid,
        "user_id": user_id,
        "bid_type": bid_type,
        "amount": amount,
        "daily_limit": daily_limit,
        "created_at": datetime.datetime.utcnow(),
    }

    bids_col.insert_one(new_bid)
    flash("Bid settings saved.", "user_success")
    return redirect(url_for("user_dashboard.dashboard"))
