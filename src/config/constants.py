"""
Global constant values used throughout the DCorp backend.

All dynamic values (DB URLs, secrets, API endpoints)
must remain in settings.py, not here.
This file only stores static constants that never change
across environments (dev, staging, production).
"""

# ======================================================================
# USER ROLES
# ======================================================================

ROLE_USER = "user"
ROLE_ADVERTISER = "advertiser"
ROLE_ADMIN = "admin"

VALID_ROLES = {ROLE_USER, ROLE_ADVERTISER, ROLE_ADMIN}


# ======================================================================
# AD SLOT DEFINITIONS (fallback defaults)
# These are used only when the child app (TT, VaultPass)
# does not override slot definitions.
# ======================================================================

DEFAULT_AD_SLOTS = [
    "homepage_top",
    "homepage_middle",
    "homepage_bottom",
    "sidebar_square",
    "sidebar_vertical",
    "app_banner",
    "video_pre_roll",
]


# ======================================================================
# BILLING & WALLET CONSTANTS
# These should NEVER depend on environment variables.
# ======================================================================

MINIMUM_WALLET_BALANCE = 0.0
DEFAULT_WALLET_CREDITS = 0.0

TRANSACTION_TYPE_DEBIT = "debit"
TRANSACTION_TYPE_CREDIT = "credit"

# Fallback bid prices (child apps or admin UI can override)
DEFAULT_CPC = 2.0     # Cost per click
DEFAULT_CPM = 10.0    # Cost per 1000 impressions


# ======================================================================
# AD EVENT TYPES (tracking)
# ======================================================================

EVENT_IMPRESSION = "impression"
EVENT_CLICK = "click"

VALID_TRACKING_EVENTS = {EVENT_IMPRESSION, EVENT_CLICK}


# ======================================================================
# PRODUCT TYPES (cross-platform integration)
# Helpful when DCorp handles multiple products.
# ======================================================================

PRODUCT_TYPE_TT = "timeless_threads"
PRODUCT_TYPE_VAULTPASS = "vaultpass"

VALID_PRODUCT_TYPES = {PRODUCT_TYPE_TT, PRODUCT_TYPE_VAULTPASS}


# ======================================================================
# ERROR MESSAGES (consistent API responses)
# Do NOT modify these messages dynamically.
# ======================================================================

ERR_UNAUTHORIZED = "Unauthorized access"
ERR_FORBIDDEN = "Forbidden"
ERR_INVALID_TOKEN = "Invalid or missing token"
ERR_MISSING_FIELDS = "Required fields missing"
ERR_NOT_FOUND = "Resource not found"
ERR_INVALID_REQUEST = "Invalid request"
ERR_SERVER_ERROR = "Server error"


# ======================================================================
# SYSTEM CONSTANTS
# ======================================================================

# Pagination fallback for admin panel / API
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 200

# Time constants
SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = 86400
