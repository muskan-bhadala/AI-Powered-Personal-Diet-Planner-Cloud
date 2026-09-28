"""
backend/routes/file_routes.py
POST   /api/upload        -> upload a demo file to cloud object storage
GET    /api/files         -> list this user's uploaded files (metadata)
GET    /api/files/<id>    -> download one of this user's files
DELETE /api/files/<id>    -> delete one of this user's files
"""

from flask import Blueprint, request, jsonify, send_file
import io

from cloud import database_service as db
from cloud import storage_service as storage
from backend.utils.auth_utils import login_required

file_bp = Blueprint("files", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "txt", "csv"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@file_bp.route("/api/upload", methods=["POST"])
@login_required
def upload_file(user_id):
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    uploaded = request.files["file"]
    if uploaded.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not _allowed(uploaded.filename):
        return jsonify({"error": f"File type not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}"}), 400

    file_bytes = uploaded.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return jsonify({"error": "File too large (max 5 MB)"}), 400

    storage_path = storage.upload_file(user_id, uploaded.filename, file_bytes)
    file_id = db.save_file_record(user_id, uploaded.filename, storage_path, uploaded.content_type)

    return jsonify({
        "message": "File uploaded to cloud storage",
        "file_id": file_id,
        "filename": uploaded.filename,
    }), 201


@file_bp.route("/api/files", methods=["GET"])
@login_required
def list_files(user_id):
    files = db.list_files_for_user(user_id)
    return jsonify({"files": files}), 200


@file_bp.route("/api/files/<file_id>", methods=["GET"])
@login_required
def download_file(user_id, file_id):
    record = db.get_file(file_id, user_id)  # user isolation enforced here
    if not record:
        return jsonify({"error": "File not found"}), 404
    file_bytes = storage.download_file(record["storage_path"])
    if file_bytes is None:
        return jsonify({"error": "File missing from storage"}), 404
    return send_file(
        io.BytesIO(file_bytes),
        download_name=record["filename"],
        as_attachment=True,
        mimetype=record.get("content_type") or "application/octet-stream",
    )


@file_bp.route("/api/files/<file_id>", methods=["DELETE"])
@login_required
def delete_file(user_id, file_id):
    record = db.get_file(file_id, user_id)
    if not record:
        return jsonify({"error": "File not found"}), 404
    storage.delete_file(record["storage_path"])
    db.delete_file_record(file_id, user_id)
    return jsonify({"message": "File deleted"}), 200
