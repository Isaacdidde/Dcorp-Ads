"""
Production-ready Campaign Model for DCorp.

Handles:
- CRUD operations for campaigns
- Serialization
- Budget/spend updates
- Active campaign listing for bidding engine
"""

from bson import ObjectId
from datetime import datetime
from database.connection import get_collection

campaigns_col = get_collection("campaigns")


# -------------------------------------------------------------------
# Utility: Safe ObjectId
# -------------------------------------------------------------------
def _safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# -------------------------------------------------------------------
# SERIALIZER
# -------------------------------------------------------------------
def serialize_campaign(doc):
    if not doc:
        return None

    def num(val):
        try:
            return float(val or 0)
        except:
            return 0.0

    return {
        "id": str(doc["_id"]),

        "advertiser_id": (
            str(doc.get("advertiser_id"))
            if doc.get("advertiser_id") else None
        ),

        # Basics
        "name": doc.get("name"),
        "objective": doc.get("objective"),

        # Finance
        "budget": num(doc.get("budget")),
        "spent": num(doc.get("spent")),

        # Bidding
        "bidding_type": doc.get("bidding_type"),
        "bid_amount": num(doc.get("bid_amount", 0)),

        # Scheduling
        "start_date": doc.get("start_date"),
        "end_date": doc.get("end_date"),

        # Targeting
        "age_min": doc.get("age_min"),
        "age_max": doc.get("age_max"),
        "gender": doc.get("gender"),
        "devices": doc.get("devices"),
        "locations": doc.get("locations"),
        "categories": doc.get("categories"),

        # Status
        "status": doc.get("status", "active"),

        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# -------------------------------------------------------------------
# CREATE CAMPAIGN
# -------------------------------------------------------------------
def create_campaign(data: dict):
    """
    Creates a campaign document.
    Caller must ensure fields are already validated.
    """

    now = datetime.utcnow()
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    data.setdefault("spent", 0)
    data.setdefault("status", "pending")  # default moderation state

    # Convert advertiser_id if needed
    if "advertiser_id" in data:
        oid = _safe_oid(data["advertiser_id"])
        if oid:
            data["advertiser_id"] = oid

    result = campaigns_col.insert_one(data)
    new_doc = campaigns_col.find_one({"_id": result.inserted_id})
    return serialize_campaign(new_doc)


# -------------------------------------------------------------------
# GET CAMPAIGN BY ID
# -------------------------------------------------------------------
def get_campaign_by_id(campaign_id: str):
    oid = _safe_oid(campaign_id)
    if not oid:
        return None

    doc = campaigns_col.find_one({"_id": oid})
    return serialize_campaign(doc)


# -------------------------------------------------------------------
# GET CAMPAIGNS BY ADVERTISER
# -------------------------------------------------------------------
def get_campaigns_by_advertiser(advertiser_id: str):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return []

    docs = campaigns_col.find({"advertiser_id": oid}).sort("created_at", -1)
    return [serialize_campaign(doc) for doc in docs]


# -------------------------------------------------------------------
# UPDATE CAMPAIGN STATUS
# -------------------------------------------------------------------
def update_campaign_status(campaign_id: str, status: str):
    oid = _safe_oid(campaign_id)
    if not oid:
        return None

    campaigns_col.update_one(
        {"_id": oid},
        {"$set": {"status": status, "updated_at": datetime.utcnow()}}
    )

    return get_campaign_by_id(campaign_id)


# -------------------------------------------------------------------
# ADD SPENT (Billing)
# -------------------------------------------------------------------
def add_spent(campaign_id: str, amount: float):
    """
    Deducts from campaign budget and increments spend.
    Used by billing engine (CPC/CPM).
    """
    oid = _safe_oid(campaign_id)
    if not oid:
        return None

    try:
        amount = float(amount)
    except:
        amount = 0.0

    campaigns_col.update_one(
        {"_id": oid},
        {
            "$inc": {"spent": amount, "budget": -amount},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    updated_doc = campaigns_col.find_one({"_id": oid})
    return serialize_campaign(updated_doc)


# -------------------------------------------------------------------
# DELETE CAMPAIGN
# -------------------------------------------------------------------
def delete_campaign(campaign_id: str):
    oid = _safe_oid(campaign_id)
    if not oid:
        return False

    result = campaigns_col.delete_one({"_id": oid})
    return result.deleted_count > 0


# -------------------------------------------------------------------
# ACTIVE CAMPAIGNS (for Bidding Engine)
# -------------------------------------------------------------------
def get_active_campaigns():
    docs = campaigns_col.find({
        "status": "active",
        "budget": {"$gt": 0}
    })

    return [serialize_campaign(doc) for doc in docs]


# -------------------------------------------------------------------
# GET ALL CAMPAIGNS (Admin Panel)
# -------------------------------------------------------------------
def get_all_campaigns():
    docs = campaigns_col.find().sort("created_at", -1)
    return [serialize_campaign(doc) for doc in docs]
