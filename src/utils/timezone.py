"""
Timezone Utility (Production Ready)

Provides:
- IST timezone object
- Safe datetime → IST conversion
- Helper `now_ist()` for timestamping
"""

from datetime import datetime, timedelta, timezone


# -----------------------------------------------------
# INDIAN STANDARD TIME (UTC + 5:30)
# -----------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))


# -----------------------------------------------------
# CONVERT DATETIME → IST
# -----------------------------------------------------
def to_ist(dt: datetime):
    """
    Converts any timezone-aware or naive datetime into IST.

    - If dt has no timezone (naive), assume UTC.
    - If dt already has tzinfo, convert properly.
    - If dt is None or invalid, return None.
    """
    if not isinstance(dt, datetime):
        return None

    # If timestamp is naive (no tzinfo), assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(IST)


# -----------------------------------------------------
# CURRENT IST TIME
# -----------------------------------------------------
def now_ist() -> datetime:
    """
    Returns the current time in IST.
    Useful for logging, timestamps, dashboards.
    """
    return datetime.now(IST)
