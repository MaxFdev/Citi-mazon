from urllib.parse import urlencode

from flask import Blueprint, render_template, request, url_for

from services.departments import list_departments
from services.search import parse_filters, search

user_bp = Blueprint("user", __name__, url_prefix="/user")


def _search_url(**updates) -> str:
    params = request.args.to_dict(flat=True)
    for key, value in updates.items():
        if value is None or value == "":
            params.pop(key, None)
        else:
            params[key] = str(value)
    query = urlencode(params)
    base = url_for("user.index")
    return f"{base}?{query}" if query else base


def _select_filter_url(attribute_id: str, option_id: str) -> str:
    return _search_url(**{f"filter_{attribute_id}": option_id})


@user_bp.context_processor
def user_template_helpers():
    return {
        "search_url": _search_url,
        "select_filter_url": _select_filter_url,
    }


@user_bp.get("/")
def index():
    query = request.args.get("q", "")
    department_id = request.args.get("department_id") or None
    filters = parse_filters(request.args)

    result = search(query=query, department_id=department_id, filters=filters)

    return render_template(
        "user/index.html",
        result=result,
        all_departments=list_departments(),
    )
