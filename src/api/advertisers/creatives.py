# src/api/advertisers/creatives.py
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from database.connection import get_collection
import os, uuid, datetime
from .utils import get_body, safe_oid

creatives_bp = Blueprint(
    "advertiser_creatives",
    __name__,
    url_prefix="/api/advertisers"
)

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

def allowed(filename):
    return "." in filename and filename.split(".")[-1].lower() in ALLOWED_EXT

def ensure_folder():
    folder = os.path.join(current_app.root_path, "src/static/uploads")
    os.makedirs(folder, exist_ok=True)
    return folder

@creatives_bp.route("/creative/upload", methods=["POST"])
def upload_creative():
    body = get_body(request)
    campaign_id = safe_oid(body.get("campaign_id"))

    if not campaign_id:
        return jsonify({"ok": False, "error": "Invalid campaign_id"}), 400

    file = request.files.get("creative")
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "File required"}), 400

    if not allowed(file.filename):
        return jsonify({"ok": False, "error": "Invalid image format"}), 400

    folder = ensure_folder()
    unique = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    file.save(os.path.join(folder, unique))

    image_url = f"/static/uploads/{unique}"

    doc = {
        "campaign_id": str(campaign_id),
        "image_url": image_url,
        "status": "pending",    # admin must approve
        "created_at": datetime.datetime.utcnow(),
        "updated_at": None
    }

    get_collection("ad_creatives").insert_one(doc)

    return jsonify({"ok": True, "image_url": image_url})
