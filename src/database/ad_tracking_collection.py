"""
Production-ready Ad Tracking Collection

Handles:
• Impression Logging
• Click Logging
• Generic Event Logging
• Safe Serialization
• Simple Analytics Helpers
"""

from database.connection import get_collection
from datetime import datetime


# -----------------------------------------------------
# Collection Accessor
# -----------------------------------------------------
def TRACK_COL():
    return get_collection("ad_tracking")


# -----------------------------------------------------
# Serializer
# -----------------------------------------------------
def serialize_event(doc):
    if not doc:
        return None

    return {
        "id": str(doc.get("_id")),
        "event": doc.get("event"),       # impression / click / conversion
        "campaign_id": doc.get("campaign_id"),
        "slot_id": doc.get("slot_id"),
        "ad_id": doc.get("ad_id"),

        # Metadata
        "ip": doc.get("ip"),
        "ua": doc.get("ua"),             # User-Agent for device/OS analysis

        # Timestamp
        "timestamp": doc.get("timestamp"),
    }


# -----------------------------------------------------
# INTERNAL INSERTOR
# -----------------------------------------------------
def _insert(data: dict):
    """
    Inserts event safely with timestamp.
    """
    data.setdefault("timestamp", datetime.utcnow())
    result = TRACK_COL().insert_one(data)
    return TRACK_COL().find_one({"_id": result.inserted_id})


# -----------------------------------------------------
# LOG GENERIC EVENT
# -----------------------------------------------------
def log_event(event_type: str, campaign_id: str, slot_id=None, ad_id=None, ip=None, ua=None):
    """
    Unified event logger.
    """
    doc = {
        "event": event_type,
        "campaign_id": campaign_id,
        "slot_id": slot_id,
        "ad_id": ad_id,
        "ip": ip,
        "ua": ua,
    }

    return serialize_event(_insert(doc))


# -----------------------------------------------------
# LOG IMPRESSION
# -----------------------------------------------------
def log_impression(campaign_id: str, slot_id=None, ip=None, ua=None):
    """
    Records a single impression.
    """
    return log_event("impression", campaign_id, slot_id=slot_id, ip=ip, ua=ua)


# -----------------------------------------------------
# LOG CLICK
# -----------------------------------------------------
def log_click(campaign_id: str, slot_id=None, ip=None, ua=None):
    """
    Records a single click.
    """
    return log_event("click", campaign_id, slot_id=slot_id, ip=ip, ua=ua)


# -----------------------------------------------------
# ANALYTICS HELPERS
# -----------------------------------------------------
def count_event(event_type: str, campaign_id=None):
    query = {"event": event_type}
    if campaign_id:
        query["campaign_id"] = campaign_id

    return TRACK_COL().count_documents(query)


def count_impressions(campaign_id=None):
    return count_event("impression", campaign_id)


def count_clicks(campaign_id=None):
    return count_event("click", campaign_id)


# -----------------------------------------------------
# LIST EVENTS (for debugging or admin panel)
# -----------------------------------------------------
def list_events(limit=100):
    docs = TRACK_COL().find().sort("timestamp", -1).limit(limit)
    return [serialize_event(doc) for doc in docs]
