import os

import httpx
from dotenv import load_dotenv
from flask import Flask, jsonify

load_dotenv()

app = Flask(__name__)


def check_supabase_connection(url: str, key: str) -> None:
    response = httpx.get(
        f"{url.rstrip('/')}/auth/v1/settings",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
        timeout=10.0,
    )
    response.raise_for_status()


@app.get("/")
def index():
    return jsonify({"message": "Hello from Citi-mazon"})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/health/supabase")
def health_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")

    if not url or not key:
        return jsonify({
            "supabase": "error",
            "detail": "Missing SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY",
        }), 500

    try:
        check_supabase_connection(url, key)
        return jsonify({"supabase": "connected"})
    except httpx.HTTPStatusError as exc:
        return jsonify({
            "supabase": "error",
            "detail": f"HTTP {exc.response.status_code}",
        }), 502
    except httpx.HTTPError as exc:
        return jsonify({
            "supabase": "error",
            "detail": str(exc),
        }), 502


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)
