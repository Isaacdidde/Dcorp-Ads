# src/services/ads/ad_models.py
"""
Domain factories and validation helpers for:
- Ad Creatives
- Ad Campaigns

This module ensures:
- Slot ID is valid
- ObjectId conversion is safe
- Numeric values are normalized
- Required fields exist
- Consistent timestamp fields
"""

from datetime import datetime
from bson import ObjectId

from .ad_slots import valid_slot, ensure_valid_slot_or_raise


# -----------------------------------------------------
# SAFE HELPERS
# -----------------------------------------------------
def _safe_oid(value):
    """Convert to ObjectId if valid, otherwise return None."""
    if not value:
        return None
    try:
        return ObjectId(value)
    except Exception:
        return None


def _now():
    return datetime.utcnow()


def _normalize_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


# -----------------------------------------------------
# CREATIVE FACTORY
# -----------------------------------------------------
def make_creative(
    advertiser_id: str,
    campaign_id: str,
    slot_id: str,
    image_url: str,
    redirect_url: str,
    headline: str = None,
):
    """
    Creates a validated creative object.
    """

    # Slot ID must exist in system
    ensure_valid_slot_or_raise(slot_id)

    if not image_url:
        raise ValueError("Creative requires image_url")

    if not redirect_url:
        raise ValueError("Creative requires redirect_url")

    return {
        "advertiser_id": _safe_oid(advertiser_id),
        "campaign_id": _safe_oid(campaign_id),

        "slot_id": slot_id,
        "image_url": image_url,
        "redirect_url": redirect_url,
        "headline": headline or "",

        "status": "pending",  # pending | approved | rejected | paused

        "created_at": _now(),
        "updated_at": _now(),
    }


# -----------------------------------------------------
# CAMPAIGN FACTORY
# -----------------------------------------------------
def make_campaign(
    advertiser_id: str,
    name: str,
    slot_id: str,
    bid_amount,
    daily_budget,
    total_budget,
    bidding_type="CPC",
):
    """
    Creates a validated campaign document.
    Ensures:
        - slot exists
        - budgets normalized
        - bidding type normalized
    """

    if not name:
        raise ValueError("Campaign requires a name")

    ensure_valid_slot_or_raise(slot_id)

    bid_amount = _normalize_float(bid_amount)
    daily_budget = _normalize_float(daily_budget)
    total_budget = _normalize_float(total_budget)

    if bid_amount <= 0:
        raise ValueError("Bid amount must be greater than zero")

    if total_budget <= 0:
        raise ValueError("Total budget must be greater than zero")

    bidding_type = (bidding_type or "CPC").upper()
    if bidding_type not in ("CPC", "CPM"):
        raise ValueError("Invalid bidding_type, allowed: CPC, CPM")

    return {
        "advertiser_id": _safe_oid(advertiser_id),

        "name": name,
        "slot_id": slot_id,

        "bid_amount": bid_amount,
        "daily_budget": daily_budget,
        "total_budget": total_budget,

        "remaining_budget": total_budget,
        "spent": 0.0,

        "bidding_type": bidding_type,

        "status": "pending",  # pending | approved | paused | ended | rejected

        "created_at": _now(),
        "updated_at": _now(),
    }


# -----------------------------------------------------
# UPDATE HELPERS
# -----------------------------------------------------
def update_timestamp(doc: dict):
    """
    Mutates a document by setting updated_at timestamp.
    """
    doc["updated_at"] = _now()
    return doc
