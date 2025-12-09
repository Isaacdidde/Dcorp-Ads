# src/api/user/billing.py

from flask import Blueprint, render_template, session, redirect, url_for, current_app
from database.connection import get_collection
from bson import ObjectId
import datetime
import calendar

billing_bp = Blueprint("user_billing", __name__, template_folder="../../templates/user")


# ----------------------------------------------------
# Helper: Standard date key (safe version)
# ----------------------------------------------------
def date_key(dt):
    if not isinstance(dt, datetime.datetime):
        return "unknown"
    return dt.strftime("%Y-%m-%d")


# ----------------------------------------------------
# BILLING PAGE
# ----------------------------------------------------
@billing_bp.route("/billing")
def billing_page():
    user_id = session.get("user_id")

    # ------------------------------------------------
    # AUTH CHECK
    # ------------------------------------------------
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    tx_col = get_collection("transactions")
    campaigns_col = get_collection("campaigns")

    # ------------------------------------------------
    # FETCH ALL USER TRANSACTIONS (DESC ORDER)
    # ------------------------------------------------
    try:
        txs = list(
            tx_col.find({"user_id": user_id})
            .sort("created_at", -1)
        )
    except Exception as e:
        current_app.logger.error(f"[BILLING] Failed to load transactions: {e}")
        txs = []

    # ------------------------------------------------
    # SANITIZE TRANSACTION FIELDS
    # ------------------------------------------------
    for t in txs:
        try:
            t["_id"] = str(t.get("_id"))
        except Exception:
            t["_id"] = "unknown"

        created_at = t.get("created_at")
        if isinstance(created_at, datetime.datetime):
            t["created_at_str"] = created_at.strftime("%d %b %Y, %I:%M %p")
        else:
            # Avoid crash in case old records lack timestamps
            t["created_at_str"] = "Unknown"

        t["date"] = date_key(created_at)

        raw_type = (t.get("transaction_type") or t.get("type") or "").lower()

        # CREDIT types
        if raw_type in ("credit", "wallet_topup", "refund", "refund_campaign_rejected"):
            t["display_type"] = "credit"
        else:
            t["display_type"] = "debit"

    # ------------------------------------------------
    # DAILY SPEND (REAL SPEND ONLY)
    # ------------------------------------------------
    daily_spend = {}

    for t in txs:
        raw_type = (t.get("transaction_type") or t.get("type") or "").lower()

        # only ad spend (not wallet debits)
        if raw_type not in ("ad_spend", "campaign_charge"):
            continue

        key = t.get("date", "unknown")
        amount = float(t.get("amount", 0) or 0)

        daily_spend[key] = daily_spend.get(key, 0.0) + amount

    # ------------------------------------------------
    # MONTHLY SPEND SUMMARY
    # ------------------------------------------------
    today = datetime.date.today()
    year, month = today.year, today.month

    try:
        _, days_in_month = calendar.monthrange(year, month)
    except Exception:
        days_in_month = 31  # safe fallback

    month_start = datetime.datetime(year, month, 1)
    month_end = datetime.datetime(year, month, days_in_month, 23, 59, 59)

    try:
        monthly_tx = tx_col.find({
            "user_id": user_id,
            "$or": [
                {"transaction_type": {"$in": ["ad_spend", "campaign_charge"]}},
                {"type": {"$in": ["ad_spend", "campaign_charge"]}}
            ],
            "created_at": {"$gte": month_start, "$lte": month_end}
        })
        month_spend = sum(float(t.get("amount", 0)) for t in monthly_tx)
    except Exception as e:
        current_app.logger.error(f"[BILLING] Monthly spend aggregation failed: {e}")
        month_spend = 0.0

    # ------------------------------------------------
    # CAMPAIGN-WISE SPEND SUMMARY
    # ------------------------------------------------
    try:
        campaigns = list(campaigns_col.find({"user_id": user_id}))
    except Exception as e:
        current_app.logger.error(f"[BILLING] Failed to load campaigns: {e}")
        campaigns = []

    for c in campaigns:
        try:
            c["_id"] = str(c.get("_id"))
        except Exception:
            c["_id"] = "unknown"

        c["spend"] = 0.0

    for t in txs:
        raw_type = (t.get("transaction_type") or t.get("type") or "").lower()

        if raw_type not in ("ad_spend", "campaign_charge"):
            continue

        cid = t.get("campaign_id")

        # Support older format `reason="campaign:<id>"`
        if not cid:
            reason = (t.get("reason") or "").lower()
            if reason.startswith("campaign:"):
                cid = reason.replace("campaign:", "").strip()

        if not cid:
            continue

        amount = float(t.get("amount", 0) or 0)

        for c in campaigns:
            if c["_id"] == str(cid):
                c["spend"] += amount
                break

    # ------------------------------------------------
    # RENDER FINAL RESPONSE
    # ------------------------------------------------
    return render_template(
        "user/billing.html",
        txs=txs,
        daily_spend=daily_spend,
        month_spend=round(month_spend, 2),
        campaigns=campaigns
    )
