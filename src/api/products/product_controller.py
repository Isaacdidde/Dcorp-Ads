from flask import Blueprint, jsonify, request
from database.models.product_model import (
    create_product,
    get_all_products,
    get_product_by_id,
    get_product_by_code,
    update_product,
    delete_product
)
from config.constants import ERR_MISSING_FIELDS, ERR_INVALID_REQUEST

product_bp = Blueprint("product_controller", __name__)


# -----------------------------------------------------
# CREATE / REGISTER NEW PRODUCT (Admin)
# -----------------------------------------------------
@product_bp.post("/register")
def register_product():
    try:
        data = request.get_json()

        required = ["name", "code", "description", "icon_url", "homepage_url"]
        if not data or not all(k in data for k in required):
            return jsonify({"error": ERR_MISSING_FIELDS}), 400

        product = create_product({
            "name": data["name"],
            "code": data["code"],
            "description": data["description"],
            "icon_url": data["icon_url"],
            "homepage_url": data["homepage_url"],
            "created_at": data.get("created_at")
        })

        return jsonify({
            "message": "Product registered successfully",
            "product": product
        }), 201

    except Exception as e:
        print("Register product error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500



# -----------------------------------------------------
# GET ALL PRODUCTS
# -----------------------------------------------------
@product_bp.get("/all")
def list_products():
    try:
        products = get_all_products()
        return jsonify({"count": len(products), "products": products}), 200

    except Exception as e:
        print("Get all products error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500



# -----------------------------------------------------
# GET PRODUCT BY ID
# -----------------------------------------------------
@product_bp.get("/id/<product_id>")
def fetch_product_by_id(product_id):
    try:
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        return jsonify(product), 200

    except Exception as e:
        print("Get product by ID error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500



# -----------------------------------------------------
# GET PRODUCT BY CODE (TT, VP, etc.)
# -----------------------------------------------------
@product_bp.get("/code/<code>")
def fetch_product_by_code(code):
    try:
        product = get_product_by_code(code)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        return jsonify(product), 200

    except Exception as e:
        print("Get product by code error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500



# -----------------------------------------------------
# UPDATE PRODUCT
# -----------------------------------------------------
@product_bp.put("/update/<product_id>")
def update_product_route(product_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": ERR_MISSING_FIELDS}), 400

        updated = update_product(product_id, data)
        if not updated:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product updated", "product": updated}), 200

    except Exception as e:
        print("Update product error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500



# -----------------------------------------------------
# DELETE PRODUCT
# -----------------------------------------------------
@product_bp.delete("/delete/<product_id>")
def delete_product_route(product_id):
    try:
        deleted = delete_product(product_id)
        if not deleted:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product deleted"}), 200

    except Exception as e:
        print("Delete product error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500
