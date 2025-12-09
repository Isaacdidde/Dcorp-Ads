"""
Utility Formatters

Reusable helper functions for formatting:
- MongoDB documents
- Lists of documents
- Timestamps
- Currency values
- Normalized strings
- Safe dictionary access
- ObjectId validation
"""

from datetime import datetime
from bson.objectid import ObjectId


# -----------------------------------------------------
# FORMAT SINGLE MONGO DOCUMENT
# -----------------------------------------------------
def format_document(doc: dict):
    """
    Convert a MongoDB document into a JSON-safe dictionary.

    - ObjectId  → str
    - datetime → ISO8601 string
    - Renames "_id" → "id" for API consistency
    """

    if not isinstance(doc, dict):
        return None

    formatted = {}

    for key, value in doc.items():
        if isinstance(value, ObjectId):
            formatted[key] = str(value)

        elif isinstance(value, datetime):
            # ISO8601 format for API consistency
            formatted[key] = value.isoformat()

        else:
            formatted[key] = value

    # Unify primary key name
    if "_id" in formatted:
        formatted["id"] = formatted["_id"]
        del formatted["_id"]

    return formatted


# -----------------------------------------------------
# FORMAT LIST OF DOCUMENTS
# -----------------------------------------------------
def format_list(items: list):
    """
    Apply format_document to each item in a list.
    """
    if not isinstance(items, list):
        return []
    return [format_document(i) for i in items]


# -----------------------------------------------------
# FORMAT MONEY (CURRENCY)
# -----------------------------------------------------
def format_money(amount, prefix="₹"):
    """
    Format numeric currency values safely.
    Example:
        1250.5 → "₹1,250.50"
        "100"  → "₹100.00"
    """
    try:
        value = float(amount)
    except Exception:
        value = 0.0

    return f"{prefix}{value:,.2f}"


# -----------------------------------------------------
# FORMAT DATE / DATETIME
# -----------------------------------------------------
def format_date(dt, fmt="%Y-%m-%d %H:%M:%S"):
    """
    Convert datetime → string in custom format.

    Default: `YYYY-MM-DD HH:MM:SS`
    """
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    return None


# -----------------------------------------------------
# NORMALIZE STRING
# -----------------------------------------------------
def normalize_string(text: str):
    """
    Normalize user input:
    - Strip surrounding whitespace
    - Remove duplicate spaces
    - Convert to lowercase

    "  Hello   WORLD " → "hello world"
    """
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().lower().split())


# -----------------------------------------------------
# SAFE GET FROM DICTIONARY
# -----------------------------------------------------
def safe_get(data, key, default=None):
    """
    Safe dictionary value accessor.
    Returns default if:
    - data is not a dict
    - key does not exist
    """
    if isinstance(data, dict):
        return data.get(key, default)
    return default


# -----------------------------------------------------
# OBJECTID VALIDATION
# -----------------------------------------------------
def is_valid_objectid(value):
    """
    Check if a string can be converted to a valid MongoDB ObjectId.
    """
    try:
        ObjectId(str(value))
        return True
    except Exception:
        return False
