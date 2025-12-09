# src/api/advertisers/utils.py
from bson import ObjectId

def safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None

def get_body(request):
    return request.get_json(silent=True) or request.form
