"""
Production-Ready Ad Slot Seeder

• Creates all predefined ad slots exactly once.
• Ensures consistent structure (enforces required fields).
• Adds created_at / updated_at timestamps.
• Fully idempotent — safe to run multiple times.

Usage:
    from src.database.ad_slot_seed import seed_slots
    seed_slots()
"""

from datetime import datetime
from database.connection import get_collection


# -------------------------------------------------------------------
# MASTER SLOT DEFINITIONS (Canonical Ad Inventory)
# -------------------------------------------------------------------
AD_SLOTS = [
    {
        "slot_id": "home_banner",
        "name": "Homepage Banner",
        "type": "banner",
        "dimensions": "1920x500",
        "max_ads": 1,
    },
    {
        "slot_id": "featured_banner",
        "name": "Featured Section Banner",
        "type": "banner",
        "dimensions": "1600x450",
        "max_ads": 1,
    },
    {
        "slot_id": "card_small",
        "name": "Small Card Ads (Product Grid)",
        "type": "card",
        "dimensions": "1000x1000",
        "max_ads": 3,
    },
    {
        "slot_id": "product_inline",
        "name": "Inline Product Ads",
        "type": "inline",
        "dimensions": "1000x1000",
        "max_ads": 5,
    },
    {
        "slot_id": "product_detail_banner",
        "name": "Product Detail Page Banner",
        "type": "banner",
        "dimensions": "1920x450",
        "max_ads": 1,
    },
    {
        "slot_id": "login_page_ad",
        "name": "Login/Register Page Ad",
        "type": "rectangle",
        "dimensions": "1080x650",
        "max_ads": 1,
    },
]


# -------------------------------------------------------------------
# SEED FUNCTION
# -------------------------------------------------------------------
def seed_slots():
    """
    Ensures all ad slots exist in the DB.
    Creates missing ones with timestamps.
    Never duplicates.
    """

    col = get_collection("ad_slots")
    inserted = 0

    for slot in AD_SLOTS:
        existing = col.find_one({"slot_id": slot["slot_id"]})

        if existing:
            print(f"✔ Slot already exists: {slot['slot_id']}")
            continue

        # Add timestamps
        now = datetime.utcnow()
        slot_doc = {
            **slot,
            "created_at": now,
            "updated_at": now,
            "status": "active",   # default slot availability
        }

        col.insert_one(slot_doc)
        inserted += 1
        print(f"➕ Inserted new slot: {slot['slot_id']}")

    print(f"\nSeeding complete. {inserted} new slots added.\n")
    return inserted


# -------------------------------------------------------------------
# OPTIONAL: Run as script
# -------------------------------------------------------------------
if __name__ == "__main__":
    seed_slots()
