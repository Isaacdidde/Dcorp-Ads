"""
Production-ready Advertiser Model for DCorp.

Handles:
- CRUD operations
- Wallet updates
- Admin dashboard summaries
- Secure serialization
"""

from bson import ObjectId
from datetime import datetime
from database.connection import get_collection

advertisers_col = get_collection("advertisers")


# -------------------------------------------------------------------
# Utility: Safe ObjectId conversion
# -------------------------------------------------------------------
def _safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# -------------------------------------------------------------------
# SERIALIZER: Clean output for API & Admin Panel
# -------------------------------------------------------------------
def serialize_advertiser(doc):
    if not doc:
        return None

    return {
        "id": str(doc.get("_id")),
        "name": doc.get("name"),
        "email": doc.get("email"),
        "phone": doc.get("phone"),

        "company_name": doc.get("company_name"),
        "company_website": doc.get("company_website"),

        "wallet_balance": float(doc.get("wallet_balance", 0)),
        "status": doc.get("status", "active"),            # active / suspended / banned
        "verified": bool(doc.get("verified", False)),

        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# -------------------------------------------------------------------
# CREATE ADVERTISER
# -------------------------------------------------------------------
def create_advertiser(data: dict):
    data.setdefault("wallet_balance", 0.0)
    data.setdefault("status", "active")
    data.setdefault("verified", False)

    now = datetime.utcnow()
    data["created_at"] = now
    data["updated_at"] = now

    result = advertisers_col.insert_one(data)
    new_doc = advertisers_col.find_one({"_id": result.inserted_id})

    return serialize_advertiser(new_doc)


# -------------------------------------------------------------------
# GET ADVERTISER BY ID
# -------------------------------------------------------------------
def get_advertiser_by_id(advertiser_id: str):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return None

    doc = advertisers_col.find_one({"_id": oid})
    return serialize_advertiser(doc)


# -------------------------------------------------------------------
# GET BY EMAIL (login, lookups)
# -------------------------------------------------------------------
def get_advertiser_by_email(email: str):
    doc = advertisers_col.find_one({"email": email})
    return serialize_advertiser(doc)


# -------------------------------------------------------------------
# UPDATE ADVERTISER INFO
# -------------------------------------------------------------------
def update_advertiser(advertiser_id: str, updates: dict):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return None

    updates = updates.copy()
    updates["updated_at"] = datetime.utcnow()

    advertisers_col.update_one({"_id": oid}, {"$set": updates})
    updated = advertisers_col.find_one({"_id": oid})

    return serialize_advertiser(updated)


# -------------------------------------------------------------------
# UPDATE WALLET BALANCE (add or deduct)
# Positive = credit, Negative = debit
# -------------------------------------------------------------------
def update_wallet(advertiser_id: str, amount: float):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return None

    advertisers_col.update_one(
        {"_id": oid},
        {
            "$inc": {"wallet_balance": float(amount)},
            "$set": {"updated_at": datetime.utcnow()},
        }
    )

    updated_doc = advertisers_col.find_one({"_id": oid})
    return serialize_advertiser(updated_doc)


# -------------------------------------------------------------------
# DELETE ADVERTISER
# -------------------------------------------------------------------
def delete_advertiser(advertiser_id: str):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return False

    result = advertisers_col.delete_one({"_id": oid})
    return result.deleted_count > 0


# -------------------------------------------------------------------
# LIST ALL ADVERTISERS (Admin Dashboard)
# -------------------------------------------------------------------
def get_all_advertisers():
    docs = advertisers_col.find().sort("created_at", -1)
    return [serialize_advertiser(doc) for doc in docs]


# -------------------------------------------------------------------
# TOTAL WALLET BALANCE (Admin Dashboard)
# -------------------------------------------------------------------
def get_total_wallet_balance():
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$wallet_balance"}}}
    ]

    result = list(advertisers_col.aggregate(pipeline))
    if not result:
        return 0.0

    return float(result[0]["total"])
