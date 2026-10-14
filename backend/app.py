import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

from backend.algorithms import LRUCache
from backend.db import close_db
from backend.routes import api
from pipeline import config

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

def create_app(db_path=None):
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.config["DB_PATH"] =str(db_path or config.DB_PATH)
    app.extensions["response_cache"] = LRUCache(capacity=256)
    app.register_blueprint(api, url_prefix="/api")
    app.teardown_appcontext(close_db)

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")
    
    @app.errorhandler(ValueError)
    def bad_request(error):
        return jsonify(error=str(error)), 400
    
    @app.errorhandler(FileNotFoundError)
    def missing_database(error):
        return jsonify(error=str(error)),503

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Dashboard: http://localhost:{port}")
    create_app().run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")