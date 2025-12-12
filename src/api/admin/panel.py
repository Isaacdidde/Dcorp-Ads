"""
Admin Panel Controller (Production Ready)

Features:
- Admin login/logout
- Dashboard analytics
- User list
- Campaign list, view, approve, reject, pause, resume
- Transactions list + CSV export
- Safe admin initialization in development only
"""

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, Response, current_app
)
from database.connection import get_collection
from bson import ObjectId
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from config.settings import settings

from utils.timezone import to_ist
from utils.campaign_health import compute_campaign_health
from utils.campaign_pacing import compute_pacing

import csv
import math
import io


admin_panel_bp = Blueprint(
    "admin_panel",
    __name__,
    template_folder="../../templates/admin"
)


# =====================================================================
# HELPERS
# =====================================================================

def require_admin():
    """Ensure admin is logged in."""
    return "admin_id" in session


def ensure_default_admin():
    """
    Creates default admin ONLY when DEBUG=True.
    Never runs in production.
    """

    if not settings.DEBUG:
        return

    admins = get_collection("admins")

    if admins.count_documents({}) == 0:
        admins.insert_one({
            "name": settings.ADMIN_DEFAULT_NAME,
            "email": settings.ADMIN_DEFAULT_EMAIL,
            "password": generate_password_hash(settings.ADMIN_DEFAULT_PASSWORD),
            "role": settings.ADMIN_DEFAULT_ROLE,
            "created_at": datetime.utcnow()
        })
        current_app.logger.info(f"Default admin created: {settings.ADMIN_DEFAULT_EMAIL}")


def safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


def normalize_tx_type(raw):
    return (raw or "other").lower()


# =====================================================================
# DASHBOARD
# =====================================================================

@admin_panel_bp.route("/")
def index():
    if not require_admin():
        return redirect(url_for("admin_panel.login"))

    try:
        campaigns = get_collection("campaigns")
        users = get_collection("users")
        tx = get_collection("transactions")

        impressions = get_collection("ads_impressions").count_documents({})
        clicks = get_collection("ads_clicks").count_documents({})

        stats = {
            "total_campaigns": campaigns.count_documents({}),
            "pending_campaigns": campaigns.count_documents({"status": "pending"}),
            "approved_campaigns": campaigns.count_documents({"status": "approved"}),
            "rejected_campaigns": campaigns.count_documents({"status": "rejected"}),

            "total_advertisers": users.count_documents({}),
            "transactions": tx.count_documents({}),

            "impressions": impressions,
            "clicks": clicks,
            "ctr": round((clicks / impressions * 100), 2) if impressions else 0,
        }

        latest = list(
            campaigns.find().sort("created_at", -1).limit(6)
        )

        for c in latest:
            c["_id"] = str(c["_id"])
            created = c.get("created_at", datetime.utcnow())
            c["created_at_str"] = created.strftime("%d %b %Y")

        return render_template("admin/dashboard.html", stats=stats, campaigns=latest)

    except Exception as e:
        current_app.logger.error(f"[ADMIN DASHBOARD ERROR] {e}")
        return render_template("admin/dashboard.html", stats={}, campaigns=[])


# =====================================================================
# AUTH (LOGIN / LOGOUT)
# =====================================================================

@admin_panel_bp.route("/login", methods=["GET", "POST"])
def login():
    ensure_default_admin()

    if request.method == "GET":
        return render_template("admin/login.html")

    try:
        email = request.form.get("email")
        password = request.form.get("password")

        admin = get_collection("admins").find_one({"email": email})
        if not admin:
            flash("Admin not found.", "danger")
            return render_template("admin/login.html")

        if not check_password_hash(admin["password"], password):
            flash("Incorrect password.", "danger")
            return render_template("admin/login.html")

        session.clear()
        session["admin_id"] = str(admin["_id"])
        session["role"] = admin.get("role", "admin")

        flash("Welcome Admin!", "success")
        return redirect(url_for("admin_panel.index"))

    except Exception as e:
        current_app.logger.error(f"[ADMIN LOGIN ERROR] {e}")
        flash("Unexpected error occurred.", "danger")
        return render_template("admin/login.html")


@admin_panel_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin_panel.login"))


# =====================================================================
# USERS LIST
# =====================================================================

@admin_panel_bp.route("/users")
def users():
    if not require_admin():
        return redirect(url_for("admin_panel.login"))

    try:
        users_col = get_collection("users")
        campaigns_col = get_collection("campaigns")
        tx_col = get_collection("transactions")

        users = list(users_col.find().sort("created_at", -1))

        for u in users:
            uid = str(u["_id"])
            u["_id"] = uid

            created = u.get("created_at")
            u["created_at_str"] = (
                created.strftime("%d %b %Y") if isinstance(created, datetime) else "—"
            )

            last_login = u.get("last_login")
            u["last_login"] = (
                to_ist(last_login).strftime("%d %b %Y, %I:%M %p")
                if isinstance(last_login, datetime) else "—"
            )

            u["total_campaigns"] = campaigns_col.count_documents({"user_id": uid})

            # Spend aggregation (campaign-level)
            agg = campaigns_col.aggregate([
                {"$match": {"user_id": uid}},
                {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$spend", 0]}}}}
            ])
            u["total_spend"] = next(agg, {}).get("total", 0)

            # Wallet calculation
            wallet = 0.0
            for t in tx_col.find({"user_id": uid}):
                tt = normalize_tx_type(t.get("transaction_type") or t.get("type"))
                amount = float(t.get("amount", 0) or 0)

                if tt in ("credit", "wallet_topup", "refund", "refund_campaign_rejected"):
                    wallet += amount
                elif tt in ("debit", "campaign_budget_assigned", "campaign_charge", "wallet_withdraw"):
                    wallet -= amount

            u["wallet_balance"] = round(wallet, 2)
            u["profile_pic"] = u.get("profile_pic", "/static/image/default_user.png")

        return render_template("admin/users.html", users=users)

    except Exception as e:
        current_app.logger.error(f"[ADMIN USERS ERROR] {e}")
        return render_template("admin/users.html", users=[])


# =====================================================================
# CAMPAIGNS LIST
# =====================================================================

@admin_panel_bp.route("/campaigns")
def campaigns():
    if not require_admin():
        return redirect(url_for("admin_panel.login"))

    try:
        coll = get_collection("campaigns")
        data = list(coll.find().sort("created_at", -1))

        for c in data:
            c["_id"] = str(c["_id"])
            created = c.get("created_at", datetime.utcnow())
            c["created_at_str"] = created.strftime("%d %b %Y")

        return render_template("admin/campaigns.html", campaigns=data)

    except Exception as e:
        current_app.logger.error(f"[ADMIN CAMPAIGNS ERROR] {e}")
        return render_template("admin/campaigns.html", campaigns=[])


# =====================================================================
# CAMPAIGN VIEW
# =====================================================================

@admin_panel_bp.route("/campaign/<cid>")
def view_campaign(cid):
    try:
        campaigns = get_collection("campaigns")
        creatives_col = get_collection("ad_creatives")
        users = get_collection("users")

        c = campaigns.find_one({"_id": safe_oid(cid)})
        if not c:
            return "Campaign not found", 404

        # -------- Date Formatter --------
        def format_date(val):
            if not val:
                return "—"
            try:
                if isinstance(val, str):
                    val = datetime.fromisoformat(val)
                return val.strftime("%d %b %Y")
            except:
                return "—"

        # -------- Add Date Strings for Template --------
        c["start_date_str"] = format_date(c.get("start_date"))
        c["end_date_str"] = format_date(c.get("end_date"))

        # Convert ID to string for other collections
        cid_str = str(c["_id"])

        # -------- Creative Data --------
        creative = creatives_col.find_one({"campaign_id": cid_str})
        if creative:
            c["creative_image"] = (
                creative.get("image_url")
                or url_for("static", filename="defaults/no-image.png")
            )
            c["redirect_url"] = creative.get("redirect_url")
            c["creative_status"] = creative.get("status", "pending")
            c["rejection_reason"] = creative.get("rejection_reason", "")
        else:
            c["creative_image"] = url_for("static", filename="defaults/no-image.png")
            c["redirect_url"] = None
            c["creative_status"] = "pending"

        # -------- Advertiser Info --------
        advertiser = users.find_one({"_id": safe_oid(c.get("user_id"))})
        if not advertiser:
            advertiser = {
                "_id": "Unknown",
                "name": "Unknown",
                "email": "Unknown",
                "profile_pic": "/static/image/default_user.png",
            }
        else:
            advertiser.setdefault("profile_pic", "/static/image/default_user.png")

        # -------- Health Score --------
        try:
            health = compute_campaign_health(c)
        except Exception:
            health = {"score": 0}

        # -------- Pacing --------
        try:
            pacing = compute_pacing(c)
        except Exception:
            pacing = {"status": "Unknown"}

        # -------- Render Page --------
        return render_template(
            "admin/campaign_view.html",
            c=c,
            advertiser=advertiser,
            health=health,
            pacing=pacing,
        )

    except Exception as e:
        current_app.logger.error(f"[ADMIN CAMPAIGN VIEW ERROR] {e}")
        return "Internal Server Error", 500



# =====================================================================
# CAMPAIGN PERFORMANCE
# =====================================================================

@admin_panel_bp.route("/campaign/<cid>/performance")
def campaign_performance(cid):
    if not require_admin():
        return redirect(url_for("admin_panel.login"))

    try:
        campaigns = get_collection("campaigns")
        impressions_col = get_collection("ads_impressions")
        clicks_col = get_collection("ads_clicks")

        c = campaigns.find_one({"_id": safe_oid(cid)})
        if not c:
            flash("Campaign not found.", "danger")
            return redirect(url_for("admin_panel.campaigns"))

        cid_str = str(c["_id"])

        impressions = impressions_col.count_documents({"campaign_id": cid_str})
        clicks = clicks_col.count_documents({"campaign_id": cid_str})

        bid = float(c.get("bid_amount", 0) or 0)
        bidding_type = c.get("bidding_type", "CPC").upper()

        ctr = (clicks / impressions * 100) if impressions else 0

        cpc = bid if bidding_type == "CPC" else 0
        cpm = bid if bidding_type == "CPM" else 0

        spent = float(c.get("spend", 0) or 0)
        remaining = float(c.get("budget", 0) or 0)

        timeline = [{
            "date": datetime.utcnow().strftime("%d %b"),
            "impressions": impressions,
            "clicks": clicks
        }]

        return render_template(
            "admin/campaign_performance.html",
            campaign=c,
            impressions=impressions,
            clicks=clicks,
            ctr=round(ctr, 2),
            spent=round(spent, 2),
            remaining=round(remaining, 2),
            cpc=round(cpc, 2),
            cpm=round(cpm, 2),
            timeline=timeline
        )

    except Exception as e:
        current_app.logger.error(f"[ADMIN CAMPAIGN PERFORMANCE ERROR] {e}")
        return "Internal Server Error", 500


# =====================================================================
# CAMPAIGN APPROVE / REJECT
# =====================================================================

@admin_panel_bp.route("/campaigns/approve/<cid>", methods=["POST"])
def approve_campaign(cid):
    try:
        campaigns = get_collection("campaigns")
        creatives = get_collection("ad_creatives")
        now = datetime.utcnow()

        campaigns.update_one(
            {"_id": safe_oid(cid)},
            {"$set": {"status": "approved", "creative_status": "approved", "approved_at": now}}
        )

        creatives.update_many(
            {"campaign_id": str(cid)},
            {"$set": {"status": "approved", "approved_at": now}}
        )

        flash("Campaign approved.", "success")
        return redirect(url_for("admin_panel.view_campaign", cid=cid))

    except Exception as e:
        current_app.logger.error(f"[ADMIN APPROVE CAMPAIGN ERROR] {e}")
        flash("Failed to approve campaign.", "danger")
        return redirect(url_for("admin_panel.campaigns"))


@admin_panel_bp.route("/campaigns/reject/<cid>", methods=["POST"])
def reject_campaign(cid):
    try:
        campaigns = get_collection("campaigns")
        creatives = get_collection("ad_creatives")
        tx = get_collection("transactions")

        reason = request.form.get("reason", "").strip() or "Campaign rejected by admin"

        camp = campaigns.find_one({"_id": safe_oid(cid)})
        if not camp:
            flash("Campaign not found.", "danger")
            return redirect(url_for("admin_panel.campaigns"))

        refund = float(camp.get("budget", 0) or 0)

        if refund > 0:
            tx.insert_one({
                "user_id": camp["user_id"],
                "amount": refund,
                "transaction_type": "refund_campaign_rejected",
                "message": reason,
                "campaign_id": str(camp["_id"]),
                "created_at": datetime.utcnow()
            })

        campaigns.update_one(
            {"_id": safe_oid(cid)},
            {"$set": {
                "status": "rejected",
                "creative_status": "rejected",
                "rejection_reason": reason,
                "rejected_at": datetime.utcnow()
            }}
        )

        creatives.update_many(
            {"campaign_id": str(cid)},
            {"$set": {"status": "rejected", "rejection_reason": reason}}
        )

        flash("Campaign rejected & refunded.", "warning")
        return redirect(url_for("admin_panel.view_campaign", cid=cid))

    except Exception as e:
        current_app.logger.error(f"[ADMIN REJECT CAMPAIGN ERROR] {e}")
        flash("Failed to reject campaign.", "danger")
        return redirect(url_for("admin_panel.campaigns"))


# =====================================================================
# TRANSACTIONS PAGE + CSV EXPORT
# =====================================================================

@admin_panel_bp.route("/transactions")
def transactions():
    if not require_admin():
        return redirect(url_for("admin_panel.login"))

    try:
        tx_col = get_collection("transactions")
        users_col = get_collection("users")
        camp_col = get_collection("campaigns")

        q = (request.args.get("q") or "").strip()
        tx_type = request.args.get("type", "").strip()
        date_from = request.args.get("from", "")
        date_to = request.args.get("to", "")
        export = (request.args.get("export") or "").lower()
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))

        query = {}

        # Search by user
        if q:
            user = (
                users_col.find_one({"email": q}) or
                users_col.find_one({"email": {"$regex": q, "$options": "i"}}) or
                users_col.find_one({"name": {"$regex": q, "$options": "i"}})
            )

            if not user and ObjectId.is_valid(q):
                user = users_col.find_one({"_id": ObjectId(q)})

            if user:
                query["user_id"] = str(user["_id"])
            else:
                query["message"] = {"$regex": q, "$options": "i"}

        # Filter by type
        if tx_type:
            query["$or"] = [
                {"transaction_type": tx_type},
                {"type": tx_type}
            ]

        # Date filter
        if date_from:
            try:
                dt = datetime.strptime(date_from, "%Y-%m-%d")
                query.setdefault("created_at", {})["$gte"] = dt
            except:
                pass

        if date_to:
            try:
                dt2 = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                query.setdefault("created_at", {})["$lt"] = dt2
            except:
                pass

        total_count = tx_col.count_documents(query)
        total_pages = max(1, math.ceil(total_count / per_page))
        page = max(1, min(page, total_pages))
        skip = (page - 1) * per_page

        txs = list(tx_col.find(query).sort("created_at", -1).skip(skip).limit(per_page))

        total_credit = 0.0
        total_debit = 0.0

        for t in txs:
            t["_id"] = str(t["_id"])
            tt = normalize_tx_type(t.get("transaction_type") or t.get("type"))
            amount = float(t.get("amount", 0) or 0)

            if tt in ("credit", "wallet_topup", "refund", "refund_campaign_rejected"):
                total_credit += amount
            elif tt in ("debit", "campaign_budget_assigned", "campaign_charge", "wallet_withdraw"):
                total_debit += amount

            created = t.get("created_at", datetime.utcnow())
            t["created_at_str"] = to_ist(created).strftime("%d %b %Y, %I:%M %p")

            # User email
            u = users_col.find_one({"_id": safe_oid(t.get("user_id"))})
            t["user_email"] = u["email"] if u else "Unknown"

            # Campaign name
            cid = t.get("campaign_id")
            if cid:
                camp = camp_col.find_one({"_id": safe_oid(cid)})
                t["campaign_name"] = camp.get("title") if camp else "-"
            else:
                t["campaign_name"] = "-"

            t["amount"] = amount
            t["message"] = t.get("message") or t.get("reason", "")

        net = round(total_credit - total_debit, 2)

        # --------------------------
        # CSV EXPORT
        # --------------------------
        if export:
            full = list(tx_col.find(query).sort("created_at", -1))
            rows = []

            for x in full:
                created = x.get("created_at", datetime.utcnow())
                created_str = to_ist(created).strftime("%d %b %Y, %I:%M %p")

                u = users_col.find_one({"_id": safe_oid(x.get("user_id"))})
                email = u["email"] if u else "Unknown"

                cid = x.get("campaign_id")
                camp = camp_col.find_one({"_id": safe_oid(cid)}) if cid else None
                camp_title = camp.get("title") if camp else "-"

                rows.append([
                    email,
                    x.get("transaction_type") or x.get("type") or "other",
                    x.get("amount", 0),
                    x.get("message") or x.get("reason") or "",
                    camp_title,
                    created_str,
                ])

            out = io.StringIO()
            writer = csv.writer(out)
            writer.writerow(["Email", "Type", "Amount", "Message", "Campaign", "Date"])
            writer.writerows(rows)
            out.seek(0)

            return Response(
                out.read(),
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment; filename=transactions.csv"}
            )

        # Distinct transaction types
        distinct_types = sorted({
            str(x) for x in (
                tx_col.distinct("transaction_type") + tx_col.distinct("type")
            ) if x
        })

        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total_count,
            "total_pages": total_pages
        }

        return render_template(
            "admin/transactions.html",
            txs=txs,
            total_credit=total_credit,
            total_debit=total_debit,
            net=net,
            pagination=pagination,
            q=q,
            date_from=date_from,
            date_to=date_to,
            tx_type=tx_type,
            distinct_types=distinct_types
        )

    except Exception as e:
        current_app.logger.error(f"[ADMIN TRANSACTIONS ERROR] {e}")
        return render_template("admin/transactions.html", txs=[], pagination={})


# =====================================================================
# PAUSE / RESUME
# =====================================================================

@admin_panel_bp.route("/campaigns/pause/<cid>", methods=["POST"])
def pause_campaign(cid):
    if not require_admin():
        return redirect(url_for("admin_panel.login"))

    try:
        get_collection("campaigns").update_one(
            {"_id": safe_oid(cid)},
            {"$set": {"status": "paused"}}
        )

        flash("Campaign paused.", "warning")
        return redirect(url_for("admin_panel.view_campaign", cid=cid))

    except Exception as e:
        current_app.logger.error(f"[ADMIN PAUSE CAMPAIGN ERROR] {e}")
        flash("Failed to pause campaign.", "danger")
        return redirect(url_for("admin_panel.campaigns"))


@admin_panel_bp.route("/campaigns/resume/<cid>", methods=["POST"])
def resume_campaign(cid):
    if not require_admin():
        return redirect(url_for("admin_panel.login"))

    try:
        get_collection("campaigns").update_one(
            {"_id": safe_oid(cid)},
            {"$set": {"status": "approved"}}
        )

        flash("Campaign resumed.", "success")
        return redirect(url_for("admin_panel.view_campaign", cid=cid))

    except Exception as e:
        current_app.logger.error(f"[ADMIN RESUME CAMPAIGN ERROR] {e}")
        flash("Failed to resume campaign.", "danger")
        return redirect(url_for("admin_panel.campaigns"))
