from flask import Blueprint, render_template

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.get("/")
def index():
    return render_template("user/index.html")
