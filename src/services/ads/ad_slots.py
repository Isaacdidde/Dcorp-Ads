# src/services/ads/ad_slots.py
"""
Central Ad Slot Definitions
---------------------------

Single source of truth for:
    - Slot ID
    - Slot type
    - Max ads allowed
    - Dimensions (recommended creative size)

Used by:
    - Creative upload validation
    - Admin slot management
    - Bidding engine
    - Slot seeding into DB
"""

from typing import Optional, Dict


# -----------------------------------------------------
# STATIC SLOT DEFINITIONS
# -----------------------------------------------------
AD_SLOTS: Dict[str, dict] = {
    "HOME_BANNER": {
        "id": "home_banner",
        "type": "banner",
        "max_ads": 1,
        "dimensions": "1920x500",
    },
    "FEATURED_BANNER": {
        "id": "featured_banner",
        "type": "banner",
        "max_ads": 1,
        "dimensions": "1920x450",
    },
    "CARD_SECTION": {
        "id": "card_small",
        "type": "card",
        "max_ads": 3,
        "dimensions": "800x1000",
    },
    "LOGIN_PAGE_AD": {
        "id": "login_page_ad",
        "type": "rectangle",
        "max_ads": 1,
        "dimensions": "1080x650",
    },
    "PRODUCT_INLINE": {
        "id": "product_inline",
        "type": "inline_card",
        "max_ads": 5,
        "dimensions": "800x1000",
    },
    "PRODUCT_DETAIL_BANNER": {
        "id": "product_detail_banner",
        "type": "banner",
        "max_ads": 1,
        "dimensions": "1920x450",
    },
}


# -----------------------------------------------------
# REVERSE LOOKUP MAP (slot_id → slot config)
# -----------------------------------------------------
SLOT_BY_ID = {v["id"]: v for v in AD_SLOTS.values()}


# -----------------------------------------------------
# SLOT VALIDATION
# -----------------------------------------------------
def valid_slot(slot_id: str) -> bool:
    """
    Check if slot_id exists in system.
    """
    return slot_id in SLOT_BY_ID


def get_slot(slot_id: str) -> Optional[dict]:
    """
    Returns full slot definition or None.
    """
    return SLOT_BY_ID.get(slot_id)


def get_all_slots():
    """
    Returns list of all available ad slots.
    """
    return list(SLOT_BY_ID.values())


def get_slot_dimensions(slot_id: str) -> Optional[str]:
    """
    Returns required creative dimensions for a slot.
    """
    slot = SLOT_BY_ID.get(slot_id)
    return slot.get("dimensions") if slot else None


def ensure_valid_slot_or_raise(slot_id: str):
    """
    Raises ValueError if slot_id is not valid.
    Used in admin creation & creative uploads.
    """
    if slot_id not in SLOT_BY_ID:
        raise ValueError(f"Invalid ad slot ID: {slot_id}")


def requires_one_creative(slot_id: str) -> bool:
    """
    Helper for UI validation:
    True if only one ad can exist per slot.
    """
    slot = SLOT_BY_ID.get(slot_id)
    return slot and slot.get("max_ads", 1) == 1


# -----------------------------------------------------
# FOR FUTURE DYNAMIC SLOT MANAGEMENT
# -----------------------------------------------------
def refresh_slot_definitions_from_db(db_slots: list):
    """
    Allows dynamic override of slot definitions from DB.
    Use in enterprise setups or multi-app environments.
    """
    global SLOT_BY_ID

    for slot in db_slots:
        if not slot.get("id"):
            continue
        SLOT_BY_ID[slot["id"]] = slot

    return SLOT_BY_ID
