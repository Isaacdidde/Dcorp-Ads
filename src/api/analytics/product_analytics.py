from flask import Blueprint, jsonify, request
from database.models.analytics_model import (
    get_product_analytics,
    get_stats_overview
)
from config.constants import ERR_INVALID_REQUEST

product_analytics_bp = Blueprint("product_analytics_bp", __name__)


# -----------------------------------------------------
# PRODUCT ANALYTICS (DAILY BREAKDOWN)
# -----------------------------------------------------
@product_analytics_bp.get("/product")
def fetch_product_analytics():
    try:
        product_code = request.args.get("product_code")

        if not product_code:
            return jsonify({"error": "product_code is required"}), 400

        analytics = get_product_analytics(product_code)

        return jsonify({
            "product_code": product_code,
            "analytics": analytics
        })

    except Exception as e:
        print("Product analytics error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500


# -----------------------------------------------------
# SUMMARY (TOTAL IMPRESSIONS, CLICKS, ETC.)
# -----------------------------------------------------
@product_analytics_bp.get("/summary")
def fetch_product_summary():
    try:
        product_code = request.args.get("product_code")

        if not product_code:
            return jsonify({"error": "product_code is required"}), 400

        summary = get_stats_overview(product_code)

        return jsonify({
            "product_code": product_code,
            "summary": summary
        })

    except Exception as e:
        print("Product analytics summary error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500
