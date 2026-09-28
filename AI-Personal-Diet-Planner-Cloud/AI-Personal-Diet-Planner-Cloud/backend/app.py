"""
backend/app.py

Main entrypoint for the REST API / application backend.
Run with:  python backend/app.py   (from the project root)

Architecture reminder:
    Frontend (static HTML/JS)  --HTTP-->  Flask REST API (this file)
        --> backend/routes/*         (request handling, validation)
        --> ai_engine/diet_engine.py (AI + rule-based fallback)
        --> cloud/database_service  (structured data -> SQLite, cloud-swappable)
        --> cloud/storage_service   (files/blobs -> local folder, cloud-swappable)
"""

import os
import sys

# Allow "python backend/app.py" to find the project-root packages
# (ai_engine, cloud) regardless of current working directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from cloud import database_service as db
from backend.routes.auth_routes import auth_bp
from backend.routes.profile_routes import profile_bp
from backend.routes.plan_routes import plan_bp
from backend.routes.file_routes import file_bp

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")


# CORS: allows the frontend (possibly on a different origin/port, or a
# different cloud domain after deployment) to call this API. Implemented
# manually here with zero extra dependencies (equivalent to flask-cors).
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


@app.route("/api/<path:_unused>", methods=["OPTIONS"])
def cors_preflight(_unused):
    return "", 204

app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(plan_bp)
app.register_blueprint(file_bp)


@app.route("/api/health", methods=["GET"])
def health_check():
    """Used by uptime monitors / load balancers to verify the app is alive."""
    return jsonify({"status": "ok", "service": "diet-planner-api"}), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(e):
    app.logger.exception("Unhandled server error")
    return jsonify({"error": "Internal server error"}), 500


# --- Serve the static frontend so the whole app can run from one process ---
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    full_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(full_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
