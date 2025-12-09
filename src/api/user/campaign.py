# controllers/campaign.py

from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
from database.connection import get_collection
from bson import ObjectId
import uuid, os, datetime
from werkzeug.utils import secure_filename
from api.ads.slot_definitions import AD_SLOTS
from config.settings import settings
from urllib.parse import urlparse

campaign_bp = Blueprint("campaign", __name__, template_folder="../../templates/user")

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}


# ------------------------------------------
# HELPERS
# ------------------------------------------
def _allowed(filename):
    """Check extension only — secondary MIME check included below."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def _valid_mime(file):
    """Ensure uploaded file is actually an image."""
    if not file:
        return False
    return file.mimetype.lower().startswith("image/")


def _ensure_upload_folder():
    """
    Production-safe upload folder.
    Respects UPLOAD_FOLDER from .env
    """
    folder = os.path.join(current_app.root_path, settings.UPLOAD_FOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def _safe_oid(val):
    try:
        return ObjectId(val)
    except:
        return None


def _format_money(v):
    try:
        return round(float(v or 0.0), 2)
    except:
        return 0.0


def _valid_redirect_url(url):
    """Protect against malicious redirect URLs."""
    if not url:
        return True  # Optional field
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.netloc
    except:
        return False


def _user_wallet_balance(user_id):
    """Compute wallet balance using transactions."""
    tx_col = get_collection("transactions")
    balance = 0.0

    for t in tx_col.find({"user_id": user_id}):
        amt = float(t.get("amount", 0) or 0)
        tt = (t.get("transaction_type") or t.get("type") or "").lower()

        if tt in ("credit", "wallet_topup", "refund", "refund_campaign_rejected"):
            balance += amt
        elif tt in ("debit", "ad_spend", "campaign_budget_assigned", "campaign_charge"):
            balance -= amt

    return round(balance, 2)


# ------------------------------------------
# LIST USER CAMPAIGNS
# ------------------------------------------
@campaign_bp.route("/campaigns")
def campaigns_list():
    if "user_id" not in session:
        return redirect(url_for("user_auth.login_user"))

    user_id = str(session["user_id"])
    campaigns_col = get_collection("campaigns")
    creatives_col = get_collection("ad_creatives")

    campaigns = list(campaigns_col.find({"user_id": user_id}).sort([("created_at", -1)]))

    for c in campaigns:
        cid = str(c["_id"])
        c["_id"] = cid

        created = c.get("created_at")
        c["created_at_str"] = created.strftime("%d %b %Y") if isinstance(created, datetime.datetime) else "—"

        creative = creatives_col.find_one({"campaign_id": cid})
        if creative:
            c["creative_image"] = creative.get("image_url")
            c["creative_status"] = creative.get("status")
            c["redirect_url"] = creative.get("redirect_url")
        else:
            c["creative_image"] = "/static/defaults/no-image.png"
            c["creative_status"] = "pending"

        c["budget"] = _format_money(c.get("budget", 0.0))
        c["spent"] = _format_money(c.get("spent", 0.0))

    return render_template("user/campaigns.html", campaigns=campaigns)


# ------------------------------------------
# VIEW CAMPAIGN
# ------------------------------------------
@campaign_bp.route("/campaign/<cid>")
def view_campaign(cid):
    if "user_id" not in session:
        return redirect(url_for("user_auth.login_user"))

    campaigns_col = get_collection("campaigns")
    creatives_col = get_collection("ad_creatives")

    c = campaigns_col.find_one({"_id": _safe_oid(cid)})
    if not c:
        flash("Campaign not found.", "danger")
        return redirect(url_for("campaign.campaigns_list"))

    c["_id"] = str(c["_id"])

    creative = creatives_col.find_one({"campaign_id": c["_id"]})
    if creative:
        c["creative_image"] = creative.get("image_url")
        c["creative_status"] = creative.get("status")
        c["redirect_url"] = creative.get("redirect_url")
    else:
        c["creative_image"] = "/static/defaults/no-image.png"
        c["creative_status"] = "pending"

    c["budget"] = _format_money(c.get("budget", 0.0))
    c["spent"] = _format_money(c.get("spent", 0.0))
    c["impressions"] = int(c.get("impressions", 0))
    c["clicks"] = int(c.get("clicks", 0))

    return render_template("user/view_campaign.html", campaign=c)


# ------------------------------------------
# CREATE CAMPAIGN PAGE
# ------------------------------------------
@campaign_bp.route("/campaign/create", methods=["GET"])
def create_campaign_page():
    if "user_id" not in session:
        return redirect(url_for("user_auth.login_user"))

    return render_template("user/create_campaign.html", slots=AD_SLOTS)


# ------------------------------------------
# CREATE CAMPAIGN POST
# ------------------------------------------
@campaign_bp.route("/campaign/create", methods=["POST"])
def create_campaign():
    if "user_id" not in session:
        return redirect(url_for("user_auth.login_user"))

    user_id = str(session["user_id"])

    campaigns_col = get_collection("campaigns")
    creatives_col = get_collection("ad_creatives")
    tx_col = get_collection("transactions")

    title = request.form.get("title", "").strip()
    slot_id = request.form.get("slot_id")
    bidding_type = request.form.get("bidding_type")

    if slot_id not in AD_SLOTS:
        flash("Invalid ad slot selected.", "danger")
        return redirect(url_for("campaign.create_campaign_page"))

    try:
        bid_amount = float(request.form.get("bid_amount", 0))
    except:
        bid_amount = 0.0

    try:
        budget = _format_money(float(request.form.get("budget", 0)))
    except:
        budget = 0.0

    start_date_raw = request.form.get("start_date")
    end_date_raw = request.form.get("end_date")

    start_date = datetime.datetime.strptime(start_date_raw, "%Y-%m-%d") if start_date_raw else None
    end_date = datetime.datetime.strptime(end_date_raw, "%Y-%m-%d") if end_date_raw else None

    redirect_url = request.form.get("redirect_url")
    headline = request.form.get("headline")
    description = request.form.get("description")
    product_name = request.form.get("product_name")

    if not title:
        flash("Campaign title is required.", "danger")
        return redirect(url_for("campaign.create_campaign_page"))

    if redirect_url and not _valid_redirect_url(redirect_url):
        flash("Invalid redirect URL format.", "danger")
        return redirect(url_for("campaign.create_campaign_page"))

    balance = _user_wallet_balance(user_id)
    if balance < budget:
        flash("Insufficient wallet balance.", "danger")
        return redirect(url_for("campaign.create_campaign_page"))

    # image upload required
    file = request.files.get("ad_image")
    if not file or not file.filename:
        flash("Ad image is required.", "danger")
        return redirect(url_for("campaign.create_campaign_page"))

    if not _allowed(file.filename) or not _valid_mime(file):
        flash("Invalid image format!", "danger")
        return redirect(url_for("campaign.create_campaign_page"))

    # save image
    folder = _ensure_upload_folder()
    filename = secure_filename(file.filename)
    unique = f"{uuid.uuid4().hex}_{filename}"
    file_path = os.path.join(folder, unique)
    file.save(file_path)
    image_url = f"/static/uploads/{unique}"

    campaign_doc = {
        "user_id": user_id,
        "title": title,
        "product_name": product_name,
        "slot_id": slot_id,
        "bidding_type": bidding_type,
        "bid_amount": _format_money(bid_amount),
        "budget": budget,
        "start_date": start_date,
        "end_date": end_date,
        "headline": headline,
        "description": description,
        "image_url": image_url,

        "impressions": 0,
        "clicks": 0,
        "spent": 0.0,
        "status": "pending",
        "creative_status": "pending",
        "created_at": datetime.datetime.utcnow()
    }

    res = campaigns_col.insert_one(campaign_doc)
    campaign_id = str(res.inserted_id)

    creatives_col.insert_one({
        "campaign_id": campaign_id,
        "slot_id": slot_id,
        "image_url": image_url,
        "redirect_url": redirect_url,
        "headline": headline,
        "status": "pending",
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    })

    # deduct budget
    tx_col.insert_one({
        "user_id": user_id,
        "type": "debit",
        "transaction_type": "campaign_budget_assigned",
        "amount": float(budget),
        "reason": "campaign_budget_assigned",
        "campaign_id": campaign_id,
        "ref_id": f"TXN-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "status": "completed",
        "created_at": datetime.datetime.utcnow()
    })

    flash("Campaign created successfully. It will be reviewed by admin.", "success")
    return redirect(url_for("campaign.campaigns_list"))


# ------------------------------------------
# DELETE CAMPAIGN
# ------------------------------------------
@campaign_bp.route("/campaign/delete/<cid>", methods=["POST"])
def delete_campaign(cid):
    if "user_id" not in session:
        return redirect(url_for("user_auth.login_user"))

    campaigns_col = get_collection("campaigns")
    creatives_col = get_collection("ad_creatives")
    tx_col = get_collection("transactions")

    camp = campaigns_col.find_one({"_id": _safe_oid(cid)})
    if camp:
        remaining = _format_money(camp.get("budget", 0.0))
        if remaining > 0:
            tx_col.insert_one({
                "user_id": camp.get("user_id"),
                "type": "credit",
                "transaction_type": "refund_campaign_deleted",
                "amount": float(remaining),
                "reason": "refund_for_deleted_campaign",
                "campaign_id": str(cid),
                "ref_id": f"REF-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                "status": "completed",
                "created_at": datetime.datetime.utcnow()
            })

    campaigns_col.delete_one({"_id": _safe_oid(cid)})
    creatives_col.delete_one({"campaign_id": str(cid)})

    flash("Campaign deletedSuccessfully.", "success")
    return redirect(url_for("campaign.campaigns_list"))


# ------------------------------------------
# EDIT CAMPAIGN PAGE
# ------------------------------------------
@campaign_bp.route("/campaign/edit/<cid>", methods=["GET"])
def edit_campaign_page(cid):
    if "user_id" not in session:
        return redirect(url_for("user_auth.login_user"))

    campaigns_col = get_collection("campaigns")
    creatives_col = get_collection("ad_creatives")

    c = campaigns_col.find_one({"_id": _safe_oid(cid)})
    if not c:
        flash("Campaign not found.", "danger")
        return redirect(url_for("campaign.campaigns_list"))

    c["_id"] = str(c["_id"])

    creative = creatives_col.find_one({"campaign_id": str(cid)})
    if creative:
        c["creative_image"] = creative.get("image_url")
        c["creative_status"] = creative.get("status")
        c["redirect_url"] = creative.get("redirect_url")

    c["budget"] = _format_money(c.get("budget", 0.0))
    c["spent"] = _format_money(c.get("spent", 0.0))

    return render_template("user/edit_campaign.html", campaign=c, slots=AD_SLOTS)


# ------------------------------------------
# EDIT CAMPAIGN SUBMIT
# ------------------------------------------
@campaign_bp.route("/campaign/edit/<cid>", methods=["POST"])
def edit_campaign_submit(cid):
    if "user_id" not in session:
        return redirect(url_for("user_auth.login_user"))

    campaigns_col = get_collection("campaigns")
    creatives_col = get_collection("ad_creatives")
    tx_col = get_collection("transactions")

    campaign = campaigns_col.find_one({"_id": _safe_oid(cid)})
    if not campaign:
        flash("Campaign not found.", "danger")
        return redirect(url_for("campaign.campaigns_list"))

    campaign_status = campaign.get("status", "pending")
    original_budget = _format_money(campaign.get("budget", 0.0))

    title = request.form.get("title")
    product_name = request.form.get("product_name")
    slot_id = request.form.get("slot_id")
    bidding_type = request.form.get("bidding_type")

    try:
        new_budget_val = _format_money(float(request.form.get("budget", original_budget)))
    except:
        new_budget_val = original_budget

    try:
        bid_amount = _format_money(float(request.form.get("bid_amount", campaign.get("bid_amount", 0))))
    except:
        bid_amount = _format_money(campaign.get("bid_amount", 0))

    start_date_raw = request.form.get("start_date")
    end_date_raw = request.form.get("end_date")

    start_date = datetime.datetime.strptime(start_date_raw, "%Y-%m-%d") if start_date_raw else None
    end_date = datetime.datetime.strptime(end_date_raw, "%Y-%m-%d") if end_date_raw else None

    redirect_url = request.form.get("redirect_url")
    headline = request.form.get("headline")
    description = request.form.get("description")

    if redirect_url and not _valid_redirect_url(redirect_url):
        flash("Invalid redirect URL.", "danger")
        return redirect(url_for("campaign.edit_campaign_page", cid=cid))

    if slot_id and slot_id not in AD_SLOTS:
        flash("Invalid ad slot selected.", "danger")
        return redirect(url_for("campaign.edit_campaign_page", cid=cid))

    can_edit_core = (campaign_status == "pending")

    update_data = {
        "headline": headline,
        "description": description,
        "updated_at": datetime.datetime.utcnow()
    }

    if title is not None:
        update_data["title"] = title.strip()
    if product_name is not None:
        update_data["product_name"] = product_name.strip()

    if can_edit_core:
        update_data.update({
            "slot_id": slot_id,
            "bidding_type": bidding_type,
            "bid_amount": bid_amount,
            "budget": new_budget_val,
            "start_date": start_date,
            "end_date": end_date,
        })
        campaigns_col.update_one({"_id": _safe_oid(cid)}, {"$set": update_data})

    else:
        campaigns_col.update_one({"_id": _safe_oid(cid)}, {"$set": update_data})

        if new_budget_val > original_budget:
            diff = _format_money(new_budget_val - original_budget)

            balance = _user_wallet_balance(str(session["user_id"]))
            if balance < diff:
                flash("Insufficient wallet balance.", "danger")
                return redirect(url_for("campaign.edit_campaign_page", cid=cid))

            tx_col.insert_one({
                "user_id": str(session["user_id"]),
                "type": "debit",
                "transaction_type": "campaign_budget_topup",
                "amount": float(diff),
                "reason": "campaign_budget_topup",
                "campaign_id": str(cid),
                "ref_id": f"TOPUP-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
                "status": "completed",
                "created_at": datetime.datetime.utcnow()
            })

            campaigns_col.update_one({"_id": _safe_oid(cid)}, {"$inc": {"budget": diff}})

            campaigns_col.update_one({"_id": _safe_oid(cid), "status": "ended"}, {"$set": {"status": "active"}})

    # --------------------------------------
    # CREATIVE UPDATE
    # --------------------------------------
    creative = creatives_col.find_one({"campaign_id": str(cid)})
    file = request.files.get("ad_image")

    if file and file.filename and _allowed(file.filename) and _valid_mime(file):
        folder = _ensure_upload_folder()
        filename = secure_filename(file.filename)
        unique = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(folder, unique)
        file.save(file_path)
        image_url = f"/static/uploads/{unique}"

        if creative:
            creatives_col.update_one(
                {"campaign_id": str(cid)},
                {"$set": {
                    "image_url": image_url,
                    "redirect_url": redirect_url,
                    "headline": headline,
                    "status": "pending",
                    "updated_at": datetime.datetime.utcnow()
                }}
            )

        else:
            camp_doc = campaigns_col.find_one({"_id": _safe_oid(cid)})
            creatives_col.insert_one({
                "campaign_id": str(cid),
                "slot_id": camp_doc.get("slot_id") if camp_doc else None,
                "image_url": image_url,
                "redirect_url": redirect_url,
                "headline": headline,
                "status": "pending",
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            })

    else:
        if creative:
            creatives_col.update_one(
                {"campaign_id": str(cid)},
                {"$set": {
                    "redirect_url": redirect_url,
                    "headline": headline,
                    "updated_at": datetime.datetime.utcnow()
                }}
            )
        else:
            if redirect_url or headline:
                camp_doc = campaigns_col.find_one({"_id": _safe_oid(cid)})
                creatives_col.insert_one({
                    "campaign_id": str(cid),
                    "slot_id": camp_doc.get("slot_id") if camp_doc else None,
                    "image_url": "/static/defaults/no-image.png",
                    "redirect_url": redirect_url,
                    "headline": headline,
                    "status": "pending",
                    "created_at": datetime.datetime.utcnow(),
                    "updated_at": datetime.datetime.utcnow()
                })

    flash("Campaign updated successfully.", "success")
    return redirect(url_for("campaign.campaigns_list"))
