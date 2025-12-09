"""
Production-ready Ad Slots Collection Manager.

Provides:
• Slot creation (only if missing)
• Slot retrieval
• Slot listing
• Slot serialization for APIs
• Safe and idempotent seeding

This works together with `slot_definitions.py` and `ad_slot_seed.py`.
"""

from datetime import datetime
from database.connection import get_collection


# -----------------------------------------------------
# Collection Access
# -----------------------------------------------------
def SLOT_COL():
    return get_collection("ad_slots")


# -----------------------------------------------------
# SERIALIZER — Ensures clean API output
# -----------------------------------------------------
def serialize_slot(doc):
    if not doc:
        return None

    return {
        "slot_id": doc.get("slot_id"),
        "name": doc.get("name"),
        "type": doc.get("type"),
        "dimensions": doc.get("dimensions"),
        "max_ads": doc.get("max_ads", 1),

        "status": doc.get("status", "active"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# -----------------------------------------------------
# SEED SLOTS — Idempotent
# -----------------------------------------------------
def seed_slots(slots_dict):
    """
    slots_dict should be your AD_SLOTS mapping:
    {
        "home_banner": { "id": "...", "name": "...", ... },
        "card_small": {...}
    }

    Inserts slot **only if it does not exist**.
    Never overwrites existing slot records.
    """

    col = SLOT_COL()
    inserted = 0

    for key, slot in slots_dict.items():
        slot_id = slot.get("id") or slot.get("slot_id") or key

        existing = col.find_one({"slot_id": slot_id})
        if existing:
            print(f"✔ Slot exists: {slot_id}")
            continue

        now = datetime.utcnow()

        doc = {
            "slot_id": slot_id,
            "name": slot.get("name"),
            "type": slot.get("type"),
            "dimensions": slot.get("dimensions"),
            "max_ads": slot.get("max_ads", 1),

            "status": "active",
            "created_at": now,
            "updated_at": now,
        }

        col.insert_one(doc)
        inserted += 1

        print(f"➕ Inserted slot: {slot_id}")

    print(f"Seeding complete. {inserted} new slots added.")
    return inserted


# -----------------------------------------------------
# GET A SINGLE SLOT
# -----------------------------------------------------
def get_slot(slot_id):
    doc = SLOT_COL().find_one({"slot_id": slot_id})
    return serialize_slot(doc)


# -----------------------------------------------------
# GET ALL SLOTS (Sorted)
# -----------------------------------------------------
def get_all_slots():
    docs = SLOT_COL().find().sort("slot_id", 1)
    return [serialize_slot(doc) for doc in docs]


# -----------------------------------------------------
# UPDATE SLOT (Admin)
# -----------------------------------------------------
def update_slot(slot_id, updates: dict):
    updates["updated_at"] = datetime.utcnow()
    SLOT_COL().update_one({"slot_id": slot_id}, {"$set": updates})

    doc = SLOT_COL().find_one({"slot_id": slot_id})
    return serialize_slot(doc)
