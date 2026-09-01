import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, url_for
from postgrest.exceptions import APIError

from blueprints.site import site_bp
from blueprints.user import user_bp
from blueprints.vendor import vendor_bp
from db import get_supabase

load_dotenv()


def check_supabase_connection() -> None:
    try:
        get_supabase().table("departments").select("id").limit(1).execute()
    except APIError as exc:
        # Schema not pushed yet. PostgREST is still reachable.
        if exc.code == "PGRST205":
            return
        raise


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev")

    app.register_blueprint(user_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(site_bp)

    @app.get("/")
    def index():
        return redirect(url_for("user.index"))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/health/supabase")
    def health_supabase():
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            return jsonify({
                "supabase": "error",
                "detail": "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY",
            }), 500

        try:
            check_supabase_connection()
            return jsonify({"supabase": "connected"})
        except APIError as exc:
            return jsonify({
                "supabase": "error",
                "detail": str(exc),
            }), 502
        except Exception as exc:
            return jsonify({
                "supabase": "error",
                "detail": str(exc),
            }), 502

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
