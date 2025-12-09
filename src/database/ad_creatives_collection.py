"""
Production-ready Ad Creatives Collection Handler.

Handles:
• Creating creatives
• Updating creatives safely
• Fetching creatives (single or by campaign)
• Serializing documents for API use
"""

from datetime import datetime
from bson import ObjectId
from database.connection import get_collection


# -----------------------------------------------------
# Collection accessor
# -----------------------------------------------------
def CREATIVE_COL():
    return get_collection("ad_creatives")


# -----------------------------------------------------
# Safe ObjectId
# -----------------------------------------------------
def safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# -----------------------------------------------------
# SERIALIZER — Safe API output
# -----------------------------------------------------
def serialize_creative(doc):
    if not doc:
        return None

    return {
        "id": str(doc["_id"]),
        "campaign_id": doc.get("campaign_id"),
        "slot_id": doc.get("slot_id"),

        "image_url": doc.get("image_url"),
        "video_url": doc.get("video_url"),
        "redirect_url": doc.get("redirect_url"),

        "status": doc.get("status", "pending"),       # pending / approved / rejected / paused
        "rejection_reason": doc.get("rejection_reason"),

        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# -----------------------------------------------------
# CREATE CREATIVE
# -----------------------------------------------------
def create_creative(doc: dict) -> str:
    """
    Inserts a new creative.
    Automatically populates timestamps and defaults.
    """

    now = datetime.utcnow()

    doc.setdefault("status", "pending")
    doc["created_at"] = now
    doc["updated_at"] = now

    res = CREATIVE_COL().insert_one(doc)
    return str(res.inserted_id)


# -----------------------------------------------------
# GET CREATIVE BY ID
# -----------------------------------------------------
def get_creative_by_id(creative_id: str):
    oid = safe_oid(creative_id)
    if not oid:
        return None

    doc = CREATIVE_COL().find_one({"_id": oid})
    return serialize_creative(doc)


# -----------------------------------------------------
# GET CREATIVES FOR A CAMPAIGN
# -----------------------------------------------------
def get_creatives_by_campaign(campaign_id: str):
    """
    Returns all creatives linked to a campaign.
    """

    # We DO NOT use ObjectId here because campaign_id
    # is stored as raw string in your DB (correct)
    docs = CREATIVE_COL().find({"campaign_id": campaign_id})
    return [serialize_creative(doc) for doc in docs]


# -----------------------------------------------------
# UPDATE CREATIVE
# -----------------------------------------------------
def update_creative(creative_id: str, updates: dict):
    oid = safe_oid(creative_id)
    if not oid:
        return None

    if not isinstance(updates, dict):
        return None

    updates["updated_at"] = datetime.utcnow()

    CREATIVE_COL().update_one({"_id": oid}, {"$set": updates})

    # return updated doc safely
    updated = CREATIVE_COL().find_one({"_id": oid})
    return serialize_creative(updated)


# -----------------------------------------------------
# DELETE CREATIVE
# -----------------------------------------------------
def delete_creative(creative_id: str) -> bool:
    oid = safe_oid(creative_id)
    if not oid:
        return False

    res = CREATIVE_COL().delete_one({"_id": oid})
    return res.deleted_count > 0
