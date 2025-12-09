# src/api/user/wallet.py

from flask import (
    Blueprint, request, render_template, redirect,
    session, flash, url_for, current_app
)
from database.connection import get_collection
from bson import ObjectId
import datetime
import uuid

wallet_bp = Blueprint("user_wallet", __name__, template_folder="../../templates/user")


# ----------------------------------------------------
# Utility: Safe ObjectId
# ----------------------------------------------------
def normalize_oid(_id):
    try:
        return ObjectId(_id)
    except Exception:
        return _id  # fallback for old string IDs


# ----------------------------------------------------
# Categorize transactions for UI
# ----------------------------------------------------
def categorize_transaction(t):
    tx_type = (t.get("transaction_type") or t.get("type") or "").lower()

    mapping = {
        "credit": "Top-up",
        "wallet_topup": "Top-up",
        "manual_topup": "Top-up",
        "payment_gateway_topup": "Top-up",

        "refund": "Refund",
        "refund_campaign_rejected": "Refund",

        "campaign_budget_assigned": "Campaign Budget Assigned",

        "ad_spend": "Ad Spend",
        "campaign_charge": "Ad Spend",
    }

    return mapping.get(tx_type, "Other")


# ----------------------------------------------------
# Calculate wallet balance (IGNORE ad_spend)
# ----------------------------------------------------
def calculate_balance(user_id):
    tx_col = get_collection("transactions")
    balance = 0.0

    try:
        txs = tx_col.find({"user_id": user_id})
    except Exception as e:
        current_app.logger.error(f"[WALLET] Balance query failed: {e}")
        return 0.0

    for t in txs:
        try:
            amount = float(t.get("amount", 0) or 0)
        except:
            amount = 0.0

        tx_type = (t.get("transaction_type") or t.get("type") or "").lower()

        # CREDIT TYPES
        if tx_type in ("credit", "wallet_topup", "refund",
                       "refund_campaign_rejected", "manual_topup"):
            balance += amount

        # REAL debits
        elif tx_type in ("debit", "campaign_budget_assigned", "wallet_withdraw"):
            balance -= amount

        # ad_spend is a campaign-level charge → ignored
        elif tx_type in ("ad_spend", "campaign_charge"):
            continue

    return round(balance, 2)


# ----------------------------------------------------
# Auto-pause campaigns when THEIR budget <= 0
# ----------------------------------------------------
def enforce_campaign_budget_limits(user_id):
    campaigns = get_collection("campaigns")

    try:
        campaigns.update_many(
            {
                "user_id": user_id,
                "budget": {"$lte": 0},
                "status": {"$in": ["approved", "running"]},
            },
            {"$set": {"status": "paused"}},
        )
    except Exception as e:
        current_app.logger.error(f"[WALLET] Budget enforcement failed: {e}")


# ----------------------------------------------------
# Wallet Page (GET)
# ----------------------------------------------------
@wallet_bp.route("/wallet", methods=["GET"])
def wallet_page():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    balance = calculate_balance(user_id)

    tx_col = get_collection("transactions")

    try:
        txs = list(
            tx_col.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(50)
        )
    except Exception as e:
        current_app.logger.error(f"[WALLET] Failed loading transactions: {e}")
        txs = []

    for t in txs:
        # ID
        try:
            t["_id"] = str(t["_id"])
        except:
            t["_id"] = "unknown"

        # Reference ID
        t["ref_id"] = t.get("ref_id", "N/A")

        # Timestamp conversion
        ts = t.get("created_at")
        if isinstance(ts, datetime.datetime):
            t["created_at_str"] = ts.strftime("%d %b %Y, %I:%M %p")
        else:
            t["created_at_str"] = "Unknown"

        # Categorization
        t["category"] = categorize_transaction(t)
        t["reason_label"] = t.get("reason") or t.get("message") or "—"

        # Display color/type
        if t["category"] in ("Top-up", "Refund"):
            t["display_type"] = "Credit"
            t["display_color"] = "green"
        else:
            t["display_type"] = "Debit"
            t["display_color"] = "red"

    enforce_campaign_budget_limits(user_id)

    low_balance = balance < 50

    return render_template(
        "user/wallet.html",
        balance=balance,
        txs=txs,
        low_balance=low_balance,
        paused=False,
    )


# ----------------------------------------------------
# Add Money (CREDIT)
# ----------------------------------------------------
@wallet_bp.route("/wallet/add", methods=["POST"])
def wallet_add():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("user_auth.login_page"))

    amount_raw = request.form.get("amount", "0").strip()

    try:
        amount = float(amount_raw)
    except:
        flash("Invalid amount entered.", "user_error")
        return redirect(url_for("user_wallet.wallet_page"))

    if amount <= 0:
        flash("Amount must be greater than zero.", "user_error")
        return redirect(url_for("user_wallet.wallet_page"))

    tx_col = get_collection("transactions")

    ref_id = f"TXN-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        tx_col.insert_one({
            "user_id": user_id,
            "type": "credit",
            "amount": amount,
            "reason": "wallet_topup",
            "ref_id": ref_id,
            "status": "completed",
            "created_at": datetime.datetime.utcnow(),
        })
    except Exception as e:
        current_app.logger.error(f"[WALLET] Top-up failed: {e}")
        flash("Unable to add money. Try again later.", "user_error")
        return redirect(url_for("user_wallet.wallet_page"))

    flash(f"₹{amount} added to wallet.", "user_success")
    return redirect(url_for("user_wallet.wallet_page"))


# ----------------------------------------------------
# Debit Wallet
# ----------------------------------------------------
def debit_wallet(user_id, amount, reason="wallet_debit"):
    tx_col = get_collection("transactions")

    balance = calculate_balance(user_id)
    if balance < amount:
        return False

    ref_id = f"TXN-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        tx_col.insert_one({
            "user_id": user_id,
            "type": "debit",
            "amount": amount,
            "reason": reason,
            "ref_id": ref_id,
            "status": "completed",
            "created_at": datetime.datetime.utcnow(),
        })
    except Exception as e:
        current_app.logger.error(f"[WALLET] Debit failed: {e}")
        return False

    return True


# ----------------------------------------------------
# Assign Campaign Budget (wallet → campaign)
# ----------------------------------------------------
def assign_campaign_budget(user_id, campaign_id, amount):
    campaigns = get_collection("campaigns")

    # Step 1: debit wallet
    if not debit_wallet(user_id, amount, reason="campaign_budget_assigned"):
        return False

    # Step 2: update campaign budget safely
    try:
        campaigns.update_one(
            {"_id": normalize_oid(campaign_id)},
            {"$inc": {"budget": amount}}
        )
    except Exception as e:
        current_app.logger.error(f"[WALLET] Failed updating campaign budget: {e}")
        return False

    return True
