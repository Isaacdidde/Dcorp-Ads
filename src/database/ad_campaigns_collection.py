"""
Production-ready Ad Campaigns Collection Handler.

This module provides:
• Safe creation of campaigns
• Safe retrieval of campaigns
• Budget adjustments with validation
• Consistent timestamp updates
• ID-safe operations
"""

from datetime import datetime
from bson import ObjectId
from database.connection import get_collection


# Collection accessor
def CAMPAIGNS():
    return get_collection("ad_campaigns")


# -----------------------------------------------------
# UTIL: Safe ObjectId
# -----------------------------------------------------
def safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# -----------------------------------------------------
# SERIALIZER — ensures API safe output
# -----------------------------------------------------
def serialize_campaign(doc):
    if not doc:
        return None

    return {
        "id": str(doc["_id"]),
        "user_id": str(doc.get("user_id")) if doc.get("user_id") else None,

        "slot_id": doc.get("slot_id"),
        "title": doc.get("title"),
        "status": doc.get("status", "pending"),

        "total_budget": float(doc.get("total_budget", 0)),
        "remaining_budget": float(doc.get("remaining_budget", 0)),
        "bid_amount": float(doc.get("bid_amount", 0)),

        "bidding_type": doc.get("bidding_type", "CPC"),

        "start_date": doc.get("start_date"),
        "end_date": doc.get("end_date"),

        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# -----------------------------------------------------
# CREATE CAMPAIGN
# -----------------------------------------------------
def create_campaign(doc: dict) -> str:
    """
    Creates a new campaign with safe defaults.
    Returns: new campaign ID (string)
    """

    now = datetime.utcnow()

    doc.setdefault("total_budget", 0.0)
    doc.setdefault("remaining_budget", doc.get("total_budget", 0.0))
    doc.setdefault("status", "pending")

    doc["created_at"] = now
    doc["updated_at"] = now

    result = CAMPAIGNS().insert_one(doc)
    return str(result.inserted_id)


# -----------------------------------------------------
# GET CAMPAIGN BY ID
# -----------------------------------------------------
def get_campaign(campaign_id):
    oid = safe_oid(campaign_id)
    if not oid:
        return None

    doc = CAMPAIGNS().find_one({"_id": oid})
    return serialize_campaign(doc)


# -----------------------------------------------------
# UPDATE CAMPAIGN BUDGET (deductions or additions)
# -----------------------------------------------------
def update_campaign_budget(campaign_id: str, amount: float):
    """
    Adds or subtracts from remaining_budget.
    Example: amount = -5 → deduct 5
    """

    oid = safe_oid(campaign_id)
    if not oid:
        return False

    try:
        amount = float(amount)
    except:
        return False

    now = datetime.utcnow()

    update = {
        "$inc": {"remaining_budget": amount},
        "$set": {"updated_at": now}
    }

    result = CAMPAIGNS().update_one({"_id": oid}, update)
    return result.modified_count > 0
