# src/api/user/placement.py
from flask import Blueprint, request, render_template, redirect, session, flash, url_for
from database.connection import get_collection
import datetime

placement_bp = Blueprint("placement", __name__, template_folder="../../templates/user")

PLACEMENT_OPTIONS = [
    ("homepage_banner", "Homepage Banner"),
    ("product_sidebar", "Product Page Sidebar"),
    ("category_strip", "Category Page Strip"),
    ("checkout_strip", "Checkout Page Strip"),
]

@placement_bp.route("/placement/<cid>", methods=["GET"])
def placement_page(cid):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    campaigns_col = get_collection("campaigns")
    campaign = campaigns_col.find_one({"_id": cid}) or campaigns_col.find_one({"_id": __import__("bson").ObjectId(cid)})
    if campaign:
        campaign["_id"] = str(campaign.get("_id"))
    return render_template("user/placement.html", campaign=campaign, options=PLACEMENT_OPTIONS)

@placement_bp.route("/placement/<cid>", methods=["POST"])
def placement_submit(cid):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    placement = request.form.get("placement")
    note = request.form.get("note", "")

    placements_col = get_collection("placements")
    placements_col.insert_one({
        "campaign_id": cid,
        "user_id": user_id,
        "placement": placement,
        "note": note,
        "status": "pending",
        "requested_at": datetime.datetime.utcnow(),
    })

    flash("Placement requested. Admin will review and approve.", "user_success")
    return redirect(url_for("user_dashboard.dashboard"))
