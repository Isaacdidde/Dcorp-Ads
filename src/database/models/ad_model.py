"""
Production-ready Ad Model for DCorp.

Handles CRUD operations, serialization,
and fetching creatives used by campaigns and the bidding engine.

Collection name: ad_creatives
(You may update to "ads" if your schema uses that name.)
"""

from bson import ObjectId
from datetime import datetime
from database.connection import get_collection

# Use the correct collection name from your system
ads_col = get_collection("ad_creatives")


# ----------------------------------------------------------------------
# Utility: Safe ObjectId conversion
# ----------------------------------------------------------------------
def _safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# ----------------------------------------------------------------------
# SERIALIZER: Normalize DB docs into consistent API-friendly JSON
# ----------------------------------------------------------------------
def serialize_ad(doc):
    if not doc:
        return None

    return {
        "id": str(doc.get("_id")),

        # Core identifiers
        "advertiser_id": str(doc.get("advertiser_id")) if doc.get("advertiser_id") else None,
        "campaign_id": str(doc.get("campaign_id")) if doc.get("campaign_id") else None,

        # Meta
        "title": doc.get("title"),
        "description": doc.get("description"),

        # Creative assets
        "image_url": doc.get("image_url"),
        "video_url": doc.get("video_url"),
        "redirect_url": doc.get("redirect_url"),

        # Targeting (optional)
        "age_min": doc.get("age_min"),
        "age_max": doc.get("age_max"),
        "gender": doc.get("gender"),
        "categories": doc.get("categories"),
        "devices": doc.get("devices"),
        "locations": doc.get("locations"),

        # Placement
        "slot_type": doc.get("slot_type"),

        # Lifecycle
        "status": doc.get("status", "pending"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# ----------------------------------------------------------------------
# CREATE AD
# ----------------------------------------------------------------------
def create_ad(data: dict):
    """
    Creates a new ad creative entry.
    Auto-handles ObjectId and timestamps.
    """

    # Normalize possible string IDs
    adv = data.get("advertiser_id")
    if adv:
        oid = _safe_oid(adv)
        if oid:
            data["advertiser_id"] = oid

    camp = data.get("campaign_id")
    if camp:
        oid = _safe_oid(camp)
        if oid:
            data["campaign_id"] = oid

    # Auto timestamps
    now = datetime.utcnow()
    data["created_at"] = now
    data["updated_at"] = now

    result = ads_col.insert_one(data)
    new_doc = ads_col.find_one({"_id": result.inserted_id})

    return serialize_ad(new_doc)


# ----------------------------------------------------------------------
# GET SINGLE AD
# ----------------------------------------------------------------------
def get_ad_by_id(ad_id: str):
    oid = _safe_oid(ad_id)
    if not oid:
        return None

    return serialize_ad(ads_col.find_one({"_id": oid}))


# ----------------------------------------------------------------------
# GET ADS FOR A CAMPAIGN
# ----------------------------------------------------------------------
def get_ads_by_campaign(campaign_id: str):
    oid = _safe_oid(campaign_id)
    if not oid:
        return []

    docs = ads_col.find({"campaign_id": oid})
    return [serialize_ad(doc) for doc in docs]


# ----------------------------------------------------------------------
# GET ADS FOR AN ADVERTISER
# ----------------------------------------------------------------------
def get_ads_by_advertiser(advertiser_id: str):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return []

    docs = ads_col.find({"advertiser_id": oid})
    return [serialize_ad(doc) for doc in docs]


# ----------------------------------------------------------------------
# UPDATE AD
# ----------------------------------------------------------------------
def update_ad(ad_id: str, updates: dict):
    oid = _safe_oid(ad_id)
    if not oid:
        return None

    updates["updated_at"] = datetime.utcnow()

    ads_col.update_one({"_id": oid}, {"$set": updates})
    updated = ads_col.find_one({"_id": oid})

    return serialize_ad(updated)


# ----------------------------------------------------------------------
# DELETE AD
# ----------------------------------------------------------------------
def delete_ad(ad_id: str):
    oid = _safe_oid(ad_id)
    if not oid:
        return False

    result = ads_col.delete_one({"_id": oid})
    return result.deleted_count > 0


# ----------------------------------------------------------------------
# GET ALL ACTIVE ADS → Crucial for bidding engine
# ----------------------------------------------------------------------
def get_active_ads():
    docs = ads_col.find({"status": "active"})
    return [serialize_ad(doc) for doc in docs]


# ----------------------------------------------------------------------
# GET ALL ADS → For admin dashboard
# ----------------------------------------------------------------------
def get_all_ads():
    docs = ads_col.find().sort("created_at", -1)
    return [serialize_ad(doc) for doc in docs]
