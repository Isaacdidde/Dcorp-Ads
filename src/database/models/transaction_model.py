"""
Production-ready Transaction Model for DCorp.

Handles:
• Wallet transactions
• Campaign-level spend logs
• Advertiser billing summaries
"""

from datetime import datetime
from bson import ObjectId
from database.connection import get_collection
from config.constants import (
    TRANSACTION_TYPE_CREDIT,
    TRANSACTION_TYPE_DEBIT,
)

transactions_col = get_collection("transactions")


# -----------------------------------------------------
# Utility: Safe ObjectId
# -----------------------------------------------------
def _safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# -----------------------------------------------------
# SERIALIZER
# -----------------------------------------------------
def serialize_transaction(doc):
    if not doc:
        return None

    return {
        "id": str(doc["_id"]),

        "advertiser_id": (
            str(doc.get("advertiser_id"))
            if doc.get("advertiser_id") else None
        ),

        "campaign_id": (
            str(doc.get("campaign_id"))
            if doc.get("campaign_id") else None
        ),

        "type": (doc.get("type") or doc.get("transaction_type")),
        "amount": float(doc.get("amount", 0)),

        # Some flows save balance_after, some don't — normalize it
        "balance_after": float(doc.get("balance_after", 0)),

        "description": (
            doc.get("description")
            or doc.get("reason")
            or doc.get("message")
        ),

        "timestamp": doc.get("timestamp") or doc.get("created_at"),
    }


# -----------------------------------------------------
# LOG TRANSACTION
# -----------------------------------------------------
def log_transaction(data: dict):
    """
    Expected keys:
        advertiser_id (str)
        campaign_id (str) (optional)
        type: credit / debit
        amount: float
        balance_after: float (optional)
        description: str
    """

    # Normalize IDs safely
    if "advertiser_id" in data:
        oid = _safe_oid(data["advertiser_id"])
        if oid:
            data["advertiser_id"] = oid

    if "campaign_id" in data:
        oid = _safe_oid(data["campaign_id"])
        if oid:
            data["campaign_id"] = oid

    # Always timestamp
    data.setdefault("timestamp", datetime.utcnow())

    # Insert
    result = transactions_col.insert_one(data)
    new_doc = transactions_col.find_one({"_id": result.inserted_id})
    return serialize_transaction(new_doc)


# -----------------------------------------------------
# GET ALL TRANSACTIONS FOR AN ADVERTISER
# -----------------------------------------------------
def get_transactions_by_advertiser(advertiser_id: str):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return []

    docs = (
        transactions_col
        .find({"advertiser_id": oid})
        .sort("timestamp", -1)
    )

    return [serialize_transaction(doc) for doc in docs]


# -----------------------------------------------------
# GET TRANSACTIONS FOR A CAMPAIGN
# -----------------------------------------------------
def get_transactions_by_campaign(campaign_id: str):
    oid = _safe_oid(campaign_id)
    if not oid:
        return []

    docs = (
        transactions_col
        .find({"campaign_id": oid})
        .sort("timestamp", -1)
    )

    return [serialize_transaction(doc) for doc in docs]


# -----------------------------------------------------
# SUMMARY: TOTAL SPENT BY CAMPAIGN (debits only)
# -----------------------------------------------------
def get_campaign_spend(campaign_id: str):
    oid = _safe_oid(campaign_id)
    if not oid:
        return 0.0

    pipeline = [
        {
            "$match": {
                "campaign_id": oid,
                "type": TRANSACTION_TYPE_DEBIT
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]

    result = list(transactions_col.aggregate(pipeline))
    return float(result[0]["total"]) if result else 0.0


# -----------------------------------------------------
# SUMMARY: TOTAL SPENT BY ADVERTISER (wallet debits only)
# -----------------------------------------------------
def get_total_spent_by_advertiser(advertiser_id: str):
    oid = _safe_oid(advertiser_id)
    if not oid:
        return 0.0

    pipeline = [
        {
            "$match": {
                "advertiser_id": oid,
                "type": TRANSACTION_TYPE_DEBIT
            }
        },
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]

    result = list(transactions_col.aggregate(pipeline))
    return float(result[0]["total"]) if result else 0.0
