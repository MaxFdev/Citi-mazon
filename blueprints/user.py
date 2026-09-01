from urllib.parse import urlencode

from flask import Blueprint, redirect, render_template, request, url_for

from services.departments import list_departments
from services.search import (
    parse_filters,
    parse_price_filter,
    search,
    single_result_department_id,
)

user_bp = Blueprint("user", __name__, url_prefix="/user")


def _args_as_pairs(exclude: list[tuple[str, str | None]] | None = None) -> list[tuple[str, str]]:
    exclude = exclude or []
    pairs: list[tuple[str, str]] = []
    for key in request.args:
        for value in request.args.getlist(key):
            if (key, value) in exclude or (key, None) in exclude:
                continue
            pairs.append((key, value))
    return pairs


def _url_from_pairs(pairs: list[tuple[str, str]]) -> str:
    query = urlencode(pairs, doseq=True)
    base = url_for("user.index")
    return f"{base}?{query}" if query else base


def _search_url(**updates) -> str:
    pairs = _args_as_pairs()
    rebuilt: list[tuple[str, str]] = []
    updated_keys = set(updates)

    for key, value in pairs:
        if key in updated_keys:
            continue
        rebuilt.append((key, value))

    for key, value in updates.items():
        if value is None or value == "":
            continue
        rebuilt.append((key, str(value)))

    return _url_from_pairs(rebuilt)


def _select_filter_url(attribute_id: str, option_id: str) -> str:
    return _search_url(**{f"filter_{attribute_id}": option_id})


def _remove_filter_url(param: str, value: str | None = None) -> str:
    if value is None:
        return _url_from_pairs(_args_as_pairs(exclude=[(param, None)]))
    return _url_from_pairs(_args_as_pairs(exclude=[(param, value)]))



def _remove_department_url() -> str:
    keep: list[tuple[str, str]] = []
    if request.args.get("q"):
        keep.append(("q", request.args.get("q")))
    for key in ("price_min", "price_max"):
        value = request.args.get(key)
        if value:
            keep.append((key, value))
    return _url_from_pairs(keep)


@user_bp.context_processor
def user_template_helpers():
    return {
        "search_url": _search_url,
        "select_filter_url": _select_filter_url,
        "remove_filter_url": _remove_filter_url,
        "remove_department_url": _remove_department_url,
    }


@user_bp.get("/")
def index():
    query = request.args.get("q", "")
    department_id = request.args.get("department_id") or None
    filters = parse_filters(request.args)
    price_filter = parse_price_filter(request.args)

    result = search(
        query=query,
        department_id=department_id,
        filters=filters,
        price_filter=price_filter,
    )

    # auto-select when every result is in one department
    if not department_id:
        auto_department_id = single_result_department_id(result.items)
        if auto_department_id:
            return redirect(_search_url(department_id=auto_department_id))

    return render_template(
        "user/index.html",
        result=result,
        all_departments=list_departments(),
    )
