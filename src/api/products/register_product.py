from flask import Blueprint, request, jsonify
from database.models.product_model import create_product
from config.constants import ERR_MISSING_FIELDS, ERR_INVALID_REQUEST

register_product_bp = Blueprint("register_product", __name__)


# -----------------------------------------------------
# REGISTER A NEW PRODUCT (Admin only)
# -----------------------------------------------------
@register_product_bp.post("/register")
def register_product():
    try:
        data = request.get_json()

        required = ["name", "code", "description", "icon_url", "homepage_url"]
        if not data or not all(field in data for field in required):
            return jsonify({"error": ERR_MISSING_FIELDS}), 400

        # Create product
        product = create_product({
            "name": data["name"],
            "code": data["code"],
            "description": data["description"],
            "icon_url": data["icon_url"],
            "homepage_url": data["homepage_url"],
            "created_at": data.get("created_at"),
        })

        return jsonify({
            "message": "Product registered successfully",
            "product": product
        }), 201

    except Exception as e:
        print("Register product error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500
