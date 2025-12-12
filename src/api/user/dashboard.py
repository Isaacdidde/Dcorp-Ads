# src/api/user/dashboard/dashboard.py

from flask import Blueprint, render_template, session, redirect, url_for, current_app
from database.connection import get_collection
from bson import ObjectId

# Wallet calculation
from api.user.wallet import calculate_balance

user_dashboard_bp = Blueprint(
    "user_dashboard", __name__, template_folder="../../templates/user"
)


# -------------------------------------------------------
# SAFE OBJECTID
# -------------------------------------------------------
def _safe_oid(val):
    try:
        return ObjectId(val)
    except Exception:
        return val  # fallback for invalid or old IDs


# -------------------------------------------------------
# FETCH LOGGED-IN USER INFO (Navbar)
# -------------------------------------------------------
def get_user_info():
    user_id = session.get("user_id")
    if not user_id:
        return None

    users = get_collection("users")

    try:
        user = users.find_one({"_id": _safe_oid(user_id)})
    except Exception as e:
        current_app.logger.error(f"[DASHBOARD] Failed to load user info: {e}")
        return None

    if not user:
        return None

    # -----------------------------
    # FIX: Unify profile image field
    # -----------------------------
    profile_pic = (
        user.get("profile_pic")            # new field used everywhere
        or user.get("profile_image")       # legacy field (your old uploads)
        or "/static/image/default_user.png"  # safe fallback
    )

    # Wallet balance calculation (already correct)
    wallet_balance = calculate_balance(user_id)

    return {
        "name": user.get("name") or "",
        "email": user.get("email") or "",
        "profile_pic": profile_pic,        # <-- unified final field
        "wallet_balance": wallet_balance,
    }

# -------------------------------------------------------
# USER DASHBOARD ROUTE
# -------------------------------------------------------
@user_dashboard_bp.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    oid = _safe_oid(user_id)

    campaigns_col = get_collection("campaigns")
    impressions_col = get_collection("ads_impressions")
    clicks_col = get_collection("ads_clicks")

    # ---------------- Fetch campaigns ----------------
    try:
        campaigns = list(campaigns_col.find({"user_id": str(oid)}))
    except Exception as e:
        current_app.logger.error(f"[DASHBOARD] Failed to load campaigns: {e}")
        campaigns = []

    campaign_ids = []
    total_spend = 0.0

    for c in campaigns:
        try:
            cid = str(c.get("_id"))
        except Exception:
            cid = None

        campaign_ids.append(cid)
        c["_id"] = cid

        # Safe defaults
        c.setdefault("title", "Untitled Campaign")
        c.setdefault("status", "pending")
        c.setdefault("budget", 0)
        c.setdefault("spend", 0)

        try:
            spend_value = float(c.get("spend") or 0)
        except Exception:
            spend_value = 0.0

        c["spend"] = spend_value
        total_spend += spend_value

    # ---------------- Campaign counters ----------------
    total_campaigns = len(campaigns)
    approved = len([x for x in campaigns if x.get("status") == "approved"])
    pending = len([x for x in campaigns if x.get("status") == "pending"])
    rejected = len([x for x in campaigns if x.get("status") == "rejected"])

    # ---------------- Global impressions & clicks ----------------
    impressions = clicks = 0

    if campaign_ids:
        try:
            impressions = impressions_col.count_documents({"campaign_id": {"$in": campaign_ids}})
            clicks = clicks_col.count_documents({"campaign_id": {"$in": campaign_ids}})
        except Exception as e:
            current_app.logger.error(f"[DASHBOARD] Impression/Click count failed: {e}")

    ctr = round((clicks / impressions) * 100, 2) if impressions else 0

    # ---------------- Wallet ----------------
    try:
        wallet_balance = calculate_balance(user_id)
    except Exception as e:
        current_app.logger.error(f"[DASHBOARD] Wallet calculation failed: {e}")
        wallet_balance = 0.0

    # ---------------- Final stats dict ----------------
    stats = {
        "total_campaigns": total_campaigns,
        "approved": approved,
        "pending": pending,
        "rejected": rejected,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr,
        "wallet_balance": wallet_balance,
        "total_spend": round(total_spend, 2),
    }

    user_info = get_user_info()

    return render_template(
        "user/dashboard.html",
        stats=stats,
        campaigns=campaigns,
        user_info=user_info
    )


# -------------------------------------------------------
# CAMPAIGN DETAILS PAGE
# -------------------------------------------------------
@user_dashboard_bp.route("/dashboard/campaign/<cid>")
def campaign_details(cid):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    campaigns_col = get_collection("campaigns")
    impressions_col = get_collection("ads_impressions")
    clicks_col = get_collection("ads_clicks")
    creatives_col = get_collection("ad_creatives")

    # ---------------- Fetch campaign ----------------
    try:
        campaign = campaigns_col.find_one({"_id": _safe_oid(cid), "user_id": user_id})
    except Exception as e:
        current_app.logger.error(f"[DASHBOARD] Failed to load campaign: {e}")
        campaign = None

    if not campaign:
        return "Campaign not found", 404

    cid_str = str(campaign.get("_id"))

    # ---------------- Budget ----------------
    try:
        allocated_budget = float(campaign.get("budget", 0))
    except:
        allocated_budget = 0.0

    try:
        spent = float(campaign.get("spend", 0))
    except:
        spent = 0.0

    remaining = max(allocated_budget - spent, 0)

    spend_velocity = 0
    if allocated_budget > 0:
        spend_velocity = round((spent / allocated_budget) * 100, 2)

    # ---------------- Performance ----------------
    try:
        impressions = impressions_col.count_documents({"campaign_id": cid_str})
        clicks = clicks_col.count_documents({"campaign_id": cid_str})
    except Exception as e:
        current_app.logger.error(f"[DASHBOARD] Perf aggregation failed: {e}")
        impressions = clicks = 0

    ctr = round((clicks / impressions) * 100, 2) if impressions else 0

    # ---------------- Timeline Aggregation ----------------
    imp_pipeline = [
        {"$match": {"campaign_id": cid_str}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    click_pipeline = [
        {"$match": {"campaign_id": cid_str}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    try:
        imp_data = list(impressions_col.aggregate(imp_pipeline))
        click_data = list(clicks_col.aggregate(click_pipeline))
    except Exception as e:
        current_app.logger.error(f"[DASHBOARD] Timeline aggregation failed: {e}")
        imp_data = []
        click_data = []

    timeline_labels = sorted({d.get("_id") for d in imp_data} | {d.get("_id") for d in click_data})
    imp_map = {d.get("_id"): d.get("count", 0) for d in imp_data}
    click_map = {d.get("_id"): d.get("count", 0) for d in click_data}

    timeline_impressions = [imp_map.get(day, 0) for day in timeline_labels]
    timeline_clicks = [click_map.get(day, 0) for day in timeline_labels]

    # ---------------- Creative Preview ----------------
    try:
        creative = creatives_col.find_one({"campaign_id": cid_str})
    except Exception:
        creative = None

    creative_url = url_for('static', filename='defaults/no-image.png')
    redirect_url = None
    creative_status = "No creative uploaded"

    if creative:
        creative_url = creative.get("image_url") or creative_url
        redirect_url = creative.get("redirect_url")
        creative_status = creative.get("status", "pending")

    # ---------------- Render ----------------
    return render_template(
        "user/campaign_details.html",
        campaign=campaign,

        # Stats
        impressions=impressions,
        clicks=clicks,
        ctr=ctr,
        spent=spent,
        remaining=remaining,
        allocated_budget=allocated_budget,
        spend_velocity=spend_velocity,

        # Timeline
        timeline_labels=timeline_labels,
        timeline_impressions=timeline_impressions,
        timeline_clicks=timeline_clicks,

        # Creative
        creative_url=creative_url,
        redirect_url=redirect_url,
        creative_status=creative_status,
    )
