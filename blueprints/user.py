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


def _clear_filters_url() -> str:
    keep: list[tuple[str, str]] = []
    if request.args.get("q"):
        keep.append(("q", request.args.get("q")))
    if request.args.get("department_id"):
        keep.append(("department_id", request.args.get("department_id")))
    return _url_from_pairs(keep)


def _active_filters(result) -> list[dict]:
    active: list[dict] = []

    if result.price_min:
        active.append({
            "label": f"Price min: {result.price_min}",
            "remove_url": _remove_filter_url("price_min"),
        })
    if result.price_max:
        active.append({
            "label": f"Price max: {result.price_max}",
            "remove_url": _remove_filter_url("price_max"),
        })

    for facet in result.select_facets:
        param = f"filter_{facet.attribute_id}"
        selected = request.args.get(param)
        if not selected:
            continue
        label = selected
        for option in facet.options:
            if option["option_id"] == selected:
                label = option["label"]
                break
        active.append({
            "label": f"{facet.attribute_name}: {label}",
            "remove_url": _remove_filter_url(param),
        })

    for facet in result.text_facets:
        param = f"filter_{facet.attribute_id}"
        selected_values = request.args.getlist(param)
        for value in selected_values:
            active.append({
                "label": f"{facet.attribute_name}: {value}",
                "remove_url": _remove_filter_url(param, value),
            })

    for facet in result.number_facets:
        min_param = f"filter_{facet.attribute_id}_min"
        max_param = f"filter_{facet.attribute_id}_max"
        min_value = request.args.get(min_param)
        max_value = request.args.get(max_param)
        if min_value:
            active.append({
                "label": f"{facet.attribute_name} min: {min_value}",
                "remove_url": _remove_filter_url(min_param),
            })
        if max_value:
            active.append({
                "label": f"{facet.attribute_name} max: {max_value}",
                "remove_url": _remove_filter_url(max_param),
            })

    return active


@user_bp.context_processor
def user_template_helpers():
    return {
        "search_url": _search_url,
        "select_filter_url": _select_filter_url,
        "clear_filters_url": _clear_filters_url,
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

    active_filters = _active_filters(result)

    return render_template(
        "user/index.html",
        result=result,
        all_departments=list_departments(),
        active_filters=active_filters,
    )
