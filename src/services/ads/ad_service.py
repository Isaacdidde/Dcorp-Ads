# src/services/ads/ad_service.py
# High-level API used by controllers to fetch ads.

import random
from bson import ObjectId
from database.connection import get_collection
from .bidding_engine import pick_winner
from .ad_slots import valid_slot

CREATIVES = lambda: get_collection("ad_creatives")

def _creative_to_json(c):
    if not c:
        return None
    return {
        "id": str(c.get("_id")),
        "advertiser_id": str(c.get("advertiser_id")) if c.get("advertiser_id") else None,
        "campaign_id": str(c.get("campaign_id")) if c.get("campaign_id") else None,
        "slot_id": c.get("slot_id"),
        "image_url": c.get("image_url"),
        "redirect_url": c.get("redirect_url"),
        "headline": c.get("headline"),
        "status": c.get("status"),
    }

def get_ad_for_slot(slot_id):
    """
    Returns a single winner creative (or None) for the requested slot.
    """
    if not valid_slot(slot_id):
        return None
    creative = pick_winner(slot_id)
    return _creative_to_json(creative)

def get_multiple_ads_for_slot(slot_id, limit=3):
    """
    Return a list of active creatives for a slot, shuffled.
    Useful for "product_inline" which wants multiple randomized ads.
    """
    if not valid_slot(slot_id):
        return []
    q = {"slot_id": slot_id, "status": "approved"}
    docs = list(CREATIVES().find(q).limit(limit*5))  # pull a few to shuffle
    random.shuffle(docs)
    docs = docs[:limit]
    return [_creative_to_json(d) for d in docs]
