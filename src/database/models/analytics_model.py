"""
Production-ready Analytics Model for DCorp.

Tracks:
- impressions
- clicks
- conversions (optional)
- per-product analytics
- admin dashboard summaries

Collection: analytics
"""

from database.connection import get_collection
from datetime import datetime
from bson import ObjectId

analytics_col = get_collection("analytics")

VALID_EVENTS = {"impression", "click", "conversion"}


# -------------------------------------------------------------------
# Utility: Safe ObjectId
# -------------------------------------------------------------------
def _safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# -------------------------------------------------------------------
# LOG EVENT (Impression, Click, Conversion)
# -------------------------------------------------------------------
def log_event(data: dict):
    """
    Safely logs an analytics event.
    Required fields:
        - event: impression / click / conversion
        - product_code: string
    Optional fields:
        - campaign_id
        - user_id
        - metadata
    """
    if not isinstance(data, dict):
        return None

    event = data.get("event")
    if event not in VALID_EVENTS:
        return None  # silently ignore invalid event types

    # Normalize campaign/user fields
    if "campaign_id" in data:
        oid = _safe_oid(data["campaign_id"])
        if oid:
            data["campaign_id"] = oid

    if "user_id" in data:
        oid = _safe_oid(data["user_id"])
        if oid:
            data["user_id"] = oid

    data["timestamp"] = datetime.utcnow()

    analytics_col.insert_one(data)
    return data


# -------------------------------------------------------------------
# OVERVIEW STATS (Impressions, Clicks, etc.)
# -------------------------------------------------------------------
def get_stats_overview(product_code=None):
    """
    Returns a dict like:
    {
        "impression": 1200,
        "click": 87,
        "conversion": 4
    }
    """
    match_stage = {}

    if product_code:
        match_stage["product_code"] = product_code

    pipeline = [
        {"$match": match_stage},
        {"$group": {"_id": "$event", "count": {"$sum": 1}}},
    ]

    summary = {}
    for item in analytics_col.aggregate(pipeline):
        summary[item["_id"]] = item["count"]

    # Ensure missing event types return zero
    for event in VALID_EVENTS:
        summary.setdefault(event, 0)

    return summary


# -------------------------------------------------------------------
# PRODUCT ANALYTICS (Daily breakdown)
# -------------------------------------------------------------------
def get_product_analytics(product_code):
    """
    Returns daily analytics:
    [
        {"event": "impression", "date": "2025-01-12", "count": 200},
        {"event": "click", "date": "2025-01-12", "count": 10},
        ...
    ]
    """
    if not product_code:
        return []

    pipeline = [
        {"$match": {"product_code": product_code}},
        {"$group": {
            "_id": {
                "event": "$event",
                "day": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id.day": 1}},
    ]

    results = []
    for item in analytics_col.aggregate(pipeline):
        results.append({
            "event": item["_id"]["event"],
            "date": item["_id"]["day"],
            "count": item["count"],
        })

    return results


# -------------------------------------------------------------------
# SIMPLE COUNTERS FOR ADMIN DASHBOARD
# -------------------------------------------------------------------
def count_total_impressions(product_code=None):
    query = {"event": "impression"}
    if product_code:
        query["product_code"] = product_code

    return analytics_col.count_documents(query)


def count_total_clicks(product_code=None):
    query = {"event": "click"}
    if product_code:
        query["product_code"] = product_code

    return analytics_col.count_documents(query)
