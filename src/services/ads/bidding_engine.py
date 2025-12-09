# src/services/ads/bidding_engine.py

"""
Bidding Engine (Ad Delivery)
----------------------------

Responsible for selecting the best-performing ad for a given slot.

Rules:
    - Only approved campaigns AND approved creatives participate.
    - CPC/CPM billing is NOT done here — handled in tracking API.
    - Sorting: Highest bid wins (simple auction model).
    - Ensures remaining budget before serving.
"""

from datetime import datetime
from bson import ObjectId
from flask import current_app

from database.connection import get_collection


# -----------------------------------------------------
# Remaining budget helper
# -----------------------------------------------------
def get_remaining_budget(campaign: dict) -> float:
    """Return remaining spendable budget for a campaign."""
    budget = float(campaign.get("budget", 0) or 0)
    spent = float(campaign.get("spend", 0) or 0)
    return max(0.0, budget - spent)


# -----------------------------------------------------
# Spend deduction helper (for CPM auto-billing)
# -----------------------------------------------------
def deduct_spend(campaign: dict, amount: float, reason: str = "CPM auto-deduct") -> bool:
    """
    Applies spend to a campaign and logs the transaction.
    This function *does not* get used for CPC clicks (handled in tracking API).
    """

    campaigns_col = get_collection("campaigns")
    tx_col = get_collection("transactions")

    cid = str(campaign["_id"])
    user_id = campaign.get("user_id")

    # Re-fetch latest copy to avoid stale reads
    fresh = campaigns_col.find_one({"_id": ObjectId(cid)})
    if not fresh:
        return False

    # Budget guard
    if get_remaining_budget(fresh) < amount:
        return False

    # Deduct spend atomically
    campaigns_col.update_one(
        {"_id": ObjectId(cid)},
        {"$inc": {"spend": amount}}
    )

    # Transaction log (informational only)
    tx_col.insert_one({
        "user_id": user_id,
        "campaign_id": cid,
        "type": "debit",
        "transaction_type": "ad_spend",
        "amount": float(amount),
        "created_at": datetime.utcnow(),
        "reason": reason,
        "ref_id": f"ADSPEND-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
    })

    return True


# -----------------------------------------------------
# Build absolute image URL
# -----------------------------------------------------
def build_full_url(url_path: str) -> str:
    """
    Ensures creatives always load properly by converting relative paths
    into full URLs using DCORP_API_URL.
    """

    if not url_path:
        return ""

    if url_path.startswith("http://") or url_path.startswith("https://"):
        return url_path  # Already absolute

    base = current_app.config.get("DCORP_API_URL")
    if not base:
        raise RuntimeError("DCORP_API_URL missing — configure it in .env")

    base = base.rstrip("/")
    if not url_path.startswith("/"):
        url_path = "/" + url_path

    return f"{base}{url_path}"


# -----------------------------------------------------
# Main Auction: Pick winning ad
# -----------------------------------------------------
def get_winning_ad(slot_id: str):
    """
    Selects the highest-bidding eligible ad for a given slot.

    Eligibility:
        - Campaign status == approved
        - Creative status == approved
        - Remaining budget > 0

    Returns:
        {
            "campaign_id": "...",
            "slot_id": "...",
            "image_url": "...",
            "redirect_url": "...",
            "headline": "...",
            "bidding_type": "CPC",
            "bid_amount": 2.5
        }
        or None
    """

    campaigns_col = get_collection("campaigns")
    creatives_col = get_collection("ad_creatives")

    # Fetch campaigns eligible for this slot
    campaigns = list(campaigns_col.find({
        "slot_id": slot_id,
        "status": "approved",
        "creative_status": "approved",
    }))

    eligible = []

    for campaign in campaigns:
        cid = str(campaign["_id"])

        # Ensure remaining budget
        if get_remaining_budget(campaign) <= 0:
            continue

        # Get approved creative for this campaign
        creative = creatives_col.find_one({
            "campaign_id": cid,
            "status": "approved",
        })

        if not creative:
            continue

        eligible.append((campaign, creative))

    # No ads available
    if not eligible:
        return None

    # Sort by BID descending — highest bidder wins
    eligible.sort(
        key=lambda pair: float(pair[0].get("bid_amount", 0) or 0),
        reverse=True
    )

    campaign, creative = eligible[0]
    cid = str(campaign["_id"])

    bidding_type = (campaign.get("bidding_type") or "CPC").upper()
    bid_amount = float(campaign.get("bid_amount", 0) or 0)

    # Build final image URL
    image_url = build_full_url(creative.get("image_url") or "")

    return {
        "campaign_id": cid,
        "slot_id": slot_id,
        "image_url": image_url,
        "redirect_url": creative.get("redirect_url"),
        "headline": creative.get("headline"),
        "bidding_type": bidding_type,
        "bid_amount": bid_amount,
    }
