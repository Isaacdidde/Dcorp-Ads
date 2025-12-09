"""
Production-ready Product Model for DCorp.

Products represent child applications such as
Timeless Threads (TT), VaultPass (VP), etc.
"""

from bson import ObjectId
from datetime import datetime
from database.connection import get_collection

products_col = get_collection("products")


# -----------------------------------------------------
# Utility: Safe ObjectId
# -----------------------------------------------------
def _safe_oid(value):
    try:
        return ObjectId(value)
    except Exception:
        return None


# -----------------------------------------------------
# SERIALIZER
# -----------------------------------------------------
def serialize_product(doc):
    if not doc:
        return None

    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "code": doc.get("code"),  # e.g., TT, VP

        "description": doc.get("description"),
        "icon_url": doc.get("icon_url"),
        "homepage_url": doc.get("homepage_url"),

        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# -----------------------------------------------------
# CREATE PRODUCT
# -----------------------------------------------------
def create_product(data: dict):
    """
    Creates a new product entry.
    Required fields: name, code
    Optional fields: description, icon_url, homepage_url
    """

    now = datetime.utcnow()

    data.setdefault("description", "")
    data.setdefault("icon_url", "")
    data.setdefault("homepage_url", "")

    data["created_at"] = now
    data["updated_at"] = now

    result = products_col.insert_one(data)
    new_doc = products_col.find_one({"_id": result.inserted_id})
    return serialize_product(new_doc)


# -----------------------------------------------------
# GET ALL PRODUCTS
# -----------------------------------------------------
def get_all_products():
    docs = products_col.find().sort("name", 1)
    return [serialize_product(doc) for doc in docs]


# -----------------------------------------------------
# TOTAL PRODUCT COUNT (Dashboard)
# -----------------------------------------------------
def get_total_products():
    return products_col.count_documents({})


# -----------------------------------------------------
# GET PRODUCT BY ID
# -----------------------------------------------------
def get_product_by_id(product_id: str):
    oid = _safe_oid(product_id)
    if not oid:
        return None

    doc = products_col.find_one({"_id": oid})
    return serialize_product(doc)


# -----------------------------------------------------
# GET PRODUCT BY CODE (e.g., TT, VP)
# -----------------------------------------------------
def get_product_by_code(code: str):
    if not code:
        return None

    doc = products_col.find_one({"code": code})
    return serialize_product(doc)


# -----------------------------------------------------
# UPDATE PRODUCT
# -----------------------------------------------------
def update_product(product_id: str, updates: dict):
    oid = _safe_oid(product_id)
    if not oid:
        return None

    updates["updated_at"] = datetime.utcnow()

    products_col.update_one({"_id": oid}, {"$set": updates})
    updated_doc = products_col.find_one({"_id": oid})
    return serialize_product(updated_doc)


# -----------------------------------------------------
# DELETE PRODUCT
# -----------------------------------------------------
def delete_product(product_id: str):
    oid = _safe_oid(product_id)
    if not oid:
        return False

    result = products_col.delete_one({"_id": oid})
    return result.deleted_count > 0
