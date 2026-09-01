from flask import Blueprint, render_template

vendor_bp = Blueprint("vendor", __name__, url_prefix="/vendor")


@vendor_bp.get("/")
def index():
    return render_template("vendor/index.html")
