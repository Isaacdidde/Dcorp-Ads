from flask import Blueprint, jsonify
from database.models.product_model import get_all_products
from config.constants import ERR_INVALID_REQUEST

get_products_bp = Blueprint("get_products", __name__)


# -----------------------------------------------------
# GET ALL REGISTERED PRODUCTS (TT, VaultPass, etc.)
# -----------------------------------------------------
@get_products_bp.get("/all")
def list_products():
    try:
        products = get_all_products()

        return jsonify({
            "count": len(products),
            "products": products
        }), 200

    except Exception as e:
        print("Get products error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500
