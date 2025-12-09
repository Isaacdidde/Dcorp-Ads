"""
Request Validation Utility (Production Ready)

Provides helpers for:
- Required field validation
- Type checking
- High-level schema validation
- Safe extraction from JSON bodies
- Safe casting (int/float/bool)
- Unified ValidationError for consistent error responses
"""

from flask import request
from config.constants import ERR_MISSING_FIELDS, ERR_INVALID_REQUEST


# -----------------------------------------------------
# CUSTOM VALIDATION ERROR
# -----------------------------------------------------
class ValidationError(Exception):
    """
    Raised when validation fails.
    Controllers should catch this and return a clean JSON error.
    """
    pass


# -----------------------------------------------------
# EXTRACT JSON BODY SAFELY
# -----------------------------------------------------
def get_request_json():
    """
    Safely returns JSON body or raises ValidationError if invalid/missing.
    """
    try:
        data = request.get_json(silent=True)
    except Exception:
        raise ValidationError(ERR_INVALID_REQUEST)

    if data is None:
        raise ValidationError("Request body must be JSON")

    if not isinstance(data, dict):
        raise ValidationError("JSON body must be an object")

    return data


# -----------------------------------------------------
# ENSURE REQUIRED FIELDS EXIST
# -----------------------------------------------------
def require_fields(data: dict, required: list):
    missing = [field for field in required if field not in data]
    if missing:
        raise ValidationError(f"{ERR_MISSING_FIELDS}: {', '.join(missing)}")
    return True


# -----------------------------------------------------
# TYPE CHECKING
# -----------------------------------------------------
def validate_types(data: dict, expected_types: dict):
    """
    expected_types = { "age": int, "tags": list }
    """
    for field, expected in expected_types.items():
        if field not in data:
            continue

        value = data[field]

        # Expected type can be tuple (multiple acceptable types)
        if isinstance(expected, tuple):
            if not isinstance(value, expected):
                raise ValidationError(
                    f"Field '{field}' must be one of: "
                    + ", ".join([t.__name__ for t in expected])
                )
        else:
            if not isinstance(value, expected):
                raise ValidationError(
                    f"Field '{field}' must be {expected.__name__}"
                )
    return True


# -----------------------------------------------------
# HIGH-LEVEL SCHEMA CHECK
# -----------------------------------------------------
def validate_schema(
    data: dict,
    required_fields: list = None,
    expected_types: dict = None
):
    """
    Combined validation utility.
    """
    if required_fields:
        require_fields(data, required_fields)

    if expected_types:
        validate_types(data, expected_types)

    return True


# -----------------------------------------------------
# SAFE JSON FIELD ACCESS
# -----------------------------------------------------
def get_json_field(data: dict, key, default=None):
    return data.get(key, default) if isinstance(data, dict) else default


# -----------------------------------------------------
# SAFE CASTING HELPERS
# -----------------------------------------------------
def safe_int(value, default=None):
    try:
        return int(value)
    except Exception:
        return default


def safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def safe_bool(value, default=None):
    """
    Converts various truthy/falsy notations into Python boolean.
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "1", "yes", "y"):
            return True
        if v in ("false", "0", "no", "n"):
            return False

    return default
