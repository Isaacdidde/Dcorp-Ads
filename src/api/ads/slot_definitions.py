"""
Centralized master definition of all ad slots in the Dcorp Ad Engine.

Slots define:
- ID (unique key used across DB & frontend)
- Human-readable name
- Type (Banner, Square, Inline, etc.)
- Recommended dimensions (for advertisers)
- Optional fields for future expansion (weight, priority, active status)

This file is imported by:
- Campaign creation pages
- Bidding engine
- Slot validation middleware
"""

# Production-safe static dictionary
# No dynamic mutations should ever happen at runtime.
AD_SLOTS = {
    "home_banner": {
        "id": "home_banner",
        "name": "Homepage Banner",
        "type": "Banner",
        "dimensions": "1920×500",
        "active": True
    },

    "featured_banner": {
        "id": "featured_banner",
        "name": "Featured Banner",
        "type": "Banner",
        "dimensions": "1600×450",
        "active": True
    },

    "card_small": {
        "id": "card_small",
        "name": "Small Card Ad",
        "type": "Square",
        "dimensions": "1000×1000",
        "active": True
    },

    "product_inline": {
        "id": "product_inline",
        "name": "Inline Product Ad",
        "type": "Square",
        "dimensions": "1000×1000",
        "active": True
    },

    "product_detail_banner": {
        "id": "product_detail_banner",
        "name": "Product Detail Banner",
        "type": "Banner",
        "dimensions": "1920×450",
        "active": True
    },

    "login_page_ad": {
        "id": "login_page_ad",
        "name": "Login Page Ad",
        "type": "Display",
        "dimensions": "1080×650",
        "active": True
    },
}


# -------------------------------------------------------------------
# OPTIONAL: Utility to validate slot IDs system-wide
# -------------------------------------------------------------------
def is_valid_slot(slot_id: str) -> bool:
    """Return True if slot_id exists in the production slot list."""
    return slot_id in AD_SLOTS


# -------------------------------------------------------------------
# OPTIONAL: Fetch slot metadata safely
# -------------------------------------------------------------------
def get_slot(slot_id: str):
    """Return slot definition or None."""
    return AD_SLOTS.get(slot_id)
