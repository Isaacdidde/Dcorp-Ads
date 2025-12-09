from flask import Blueprint, jsonify, request
from database.models.analytics_model import get_stats_overview
from config.constants import ERR_INVALID_REQUEST

analytics_stats_bp = Blueprint("analytics_stats_bp", __name__)


@analytics_stats_bp.get("/overview")
def stats_overview():
    try:
        product_code = request.args.get("product_code")

        stats = get_stats_overview(product_code)

        return jsonify({
            "message": "Analytics overview fetched",
            "stats": stats
        })

    except Exception as e:
        print("Stats overview error:", e)
        return jsonify({"error": ERR_INVALID_REQUEST}), 500
