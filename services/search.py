from collections import defaultdict
from dataclasses import dataclass, field

from db import get_supabase


# dataclasses for the different ways to search

@dataclass
class SelectFacet:
    attribute_id: str
    attribute_name: str
    options: list[dict] = field(default_factory=list)


@dataclass
class TextFacet:
    attribute_id: str
    attribute_name: str
    options: list[dict] = field(default_factory=list)


@dataclass
class NumberFacet:
    attribute_id: str
    attribute_name: str
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class PriceFacet:
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class SearchResult:
    query: str
    department_id: str | None
    active_departments: list[dict]
    items: list[dict]
    select_facets: list[SelectFacet]
    text_facets: list[TextFacet]
    number_facets: list[NumberFacet]
    price_facet: PriceFacet
    price_min: str | None = None
    price_max: str | None = None

# actual search

def search(
    query: str = "",
    department_id: str | None = None,
    filters: dict | None = None,
    price_filter: dict | None = None,
) -> SearchResult:
    filters = filters or {}
    price_filter = price_filter or {}
    if not department_id:
        filters = {}
    q = query.strip()
    price_min = price_filter.get("min")
    price_max = price_filter.get("max")

    departments = _list_departments()
    term_matched = _departments_matching_terms(q, departments) if q else []

    items = _fetch_items(q, department_id, price_filter)

    # get departments that have at least one item that matches
    item_department_ids = {item["department_id"] for item in items}
    item_matched = [dept for dept in departments if dept["id"] in item_department_ids]
    active = _merge_departments(term_matched, item_matched)

    # filter by provided department
    if department_id:
        active = [dept for dept in active if dept["id"] == department_id]

        # make sure that selected departments appear even if they don't match
        if not active:
            active = [dept for dept in departments if dept["id"] == department_id]

    item_attrs_by_item = _load_item_attributes([item["id"] for item in items])
    text_facets: list[TextFacet] = []

    # attribute filters only when a department is selected
    if department_id:
        attributes = _attributes_for_departments({department_id})
        items = _apply_filters(items, item_attrs_by_item, attributes, filters)

        # drop attribute rows for items filtered out
        item_attrs_by_item = {
            item_id: attrs
            for item_id, attrs in item_attrs_by_item.items()
            if item_id in {item["id"] for item in items}
        }
        select_facets, text_facets, number_facets = _build_facets(
            items, item_attrs_by_item, attributes
        )
    else:
        # no department picked yet, so no attribute filters
        select_facets, number_facets = [], []

    # attach attributes onto each item for the results list
    for item in items:
        item["item_attributes"] = item_attrs_by_item.get(item["id"], [])

    return SearchResult(
        query=q,
        department_id=department_id,
        active_departments=active,
        items=items,
        select_facets=select_facets,
        text_facets=text_facets,
        number_facets=number_facets,
        price_facet=_build_price_facet(items),
        price_min=price_min,
        price_max=price_max,
    )


def parse_filters(args) -> dict:
    """Turn query params like filter_<id>=opt into a filter spec dict."""
    filters: dict = {}
    keys = args.keys() if hasattr(args, "keys") else args

    for key in keys:
        if not key.startswith("filter_"):
            continue

        body = key.removeprefix("filter_")

        # number range lower bound
        if body.endswith("_min"):
            attr_id = body.removesuffix("_min")
            value = _arg_value(args, key)
            if value:
                filters.setdefault(attr_id, {})["min"] = value
            continue

        # number range upper bound
        if body.endswith("_max"):
            attr_id = body.removesuffix("_max")
            value = _arg_value(args, key)
            if value:
                filters.setdefault(attr_id, {})["max"] = value
            continue

        # select option id or text values (checkboxes use getlist)
        values = _arg_values(args, key)
        if not values:
            continue
        if len(values) == 1:
            filters[body] = {"option_id": values[0]}
        else:
            filters[body] = {"values": values}

    return filters


def parse_price_filter(args) -> dict:
    """pull price_min / price_max out of the query string."""
    price_filter: dict = {}
    price_min = _arg_value(args, "price_min")
    price_max = _arg_value(args, "price_max")
    if price_min:
        price_filter["min"] = price_min
    if price_max:
        price_filter["max"] = price_max
    return price_filter


def single_result_department_id(items: list[dict]) -> str | None:
    """when every item is in the same department, return that id."""
    if not items:
        return None
    department_ids = {
        item["department_id"]
        for item in items
        if item.get("department_id")
    }
    if len(department_ids) != 1:
        return None
    return next(iter(department_ids))


def _arg_value(args, key: str) -> str | None:
    if hasattr(args, "get"):
        value = args.get(key)
    else:
        value = args.get(key) if isinstance(args, dict) else None
    if value is None or value == "":
        return None
    return str(value)


def _arg_values(args, key: str) -> list[str]:
    if hasattr(args, "getlist"):
        return [str(value) for value in args.getlist(key) if value]
    value = _arg_value(args, key)
    return [value] if value else []


def _list_departments() -> list[dict]:
    response = (
        get_supabase()
        .table("departments")
        .select("id, name, description, search_terms")
        .order("name")
        .execute()
    )
    return response.data


def _departments_matching_terms(query: str, departments: list[dict]) -> list[dict]:
    lower = query.lower()
    matched = []

    for department in departments:
        # check if lower is in search terms or department name
        terms = " ".join(department.get("search_terms") or []).lower()
        name = department.get("name", "").lower()
        if lower in terms or lower in name:
            matched.append(department)

    return matched


def _merge_departments(*groups: list[dict]) -> list[dict]:
    # dedupe departments that match on term and item
    merged: dict[str, dict] = {}
    for group in groups:
        for department in group:
            merged[department["id"]] = department
    return list(merged.values())


def _fetch_items(
    query: str,
    department_id: str | None,
    price_filter: dict | None = None,
) -> list[dict]:
    price_filter = price_filter or {}
    request = (
        get_supabase()
        .table("items")
        .select("id, department_id, vendor_name, title, description, price, departments(name)")
        .limit(50)
    )

    # search on title and description
    if query:
        request = request.or_(f"title.ilike.%{query}%,description.ilike.%{query}%")

    # department scope from dropdown
    if department_id:
        request = request.eq("department_id", department_id)

    # price range in the db (uses idx_items_price)
    if "min" in price_filter:
        request = request.gte("price", price_filter["min"])
    if "max" in price_filter:
        request = request.lte("price", price_filter["max"])

    return request.execute().data


def _build_price_facet(items: list[dict]) -> PriceFacet:
    if not items:
        return PriceFacet()
    prices = [float(item["price"]) for item in items]
    return PriceFacet(min_value=min(prices), max_value=max(prices))


def _attributes_for_departments(department_ids: set[str]) -> list[dict]:
    if not department_ids:
        return []

    # get options for attributes
    response = (
        get_supabase()
        .table("department_attributes")
        .select("*, attribute_options(*)")
        .in_("department_id", list(department_ids))
        .order("name")
        .execute()
    )
    return response.data


def _load_item_attributes(item_ids: list[str]) -> dict[str, list[dict]]:
    if not item_ids:
        return {}

    response = (
        get_supabase()
        .table("item_attributes")
        .select("*, department_attributes(name, attribute_type), attribute_options(value)")
        .in_("item_id", item_ids)
        .execute()
    )

    # group rows of attributes by item id
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in response.data:
        grouped[row["item_id"]].append(row)
    return grouped


def _apply_filters(
    items: list[dict],
    item_attrs_by_item: dict[str, list[dict]],
    attributes: list[dict],
    filters: dict,
) -> list[dict]:
    if not filters:
        return items

    attributes_by_id = {attribute["id"]: attribute for attribute in attributes}
    filtered = []

    for item in items:
        # index item's attributes by their id
        item_attrs = {
            row["attribute_id"]: row
            for row in item_attrs_by_item.get(item["id"], [])
        }

        # keep item if all filters match
        if all(
            _matches_filter(item_attrs.get(attr_id), attributes_by_id.get(attr_id), spec)
            for attr_id, spec in filters.items()
        ):
            filtered.append(item)

    return filtered


def _matches_filter(
    item_attr: dict | None,
    attribute: dict | None,
    spec: dict,
) -> bool:
    if item_attr is None or attribute is None:
        return False

    attr_type = attribute["attribute_type"]

    # selects must be equal to the filter
    if attr_type == "select":
        option_id = spec.get("option_id")
        if option_id is not None:
            return item_attr.get("option_id") == option_id
        return item_attr.get("option_id") in spec.get("values", [])

    # text checkboxes hide anything that doesn't match
    if attr_type == "text":
        value = item_attr.get("value_text")
        if value is None:
            return False
        values = spec.get("values")
        if values is not None:
            return value in values
        option_id = spec.get("option_id")
        return option_id is not None and value == option_id

    # numbers need to match the range
    if attr_type == "number":
        value = item_attr.get("value_number")
        if value is None:
            return False
        if "min" in spec and float(value) < float(spec["min"]):
            return False
        if "max" in spec and float(value) > float(spec["max"]):
            return False
        return True

    return True


def _build_facets(
    items: list[dict],
    item_attrs_by_item: dict[str, list[dict]],
    attributes: list[dict],
) -> tuple[list[SelectFacet], list[TextFacet], list[NumberFacet]]:
    select_facets: list[SelectFacet] = []
    text_facets: list[TextFacet] = []
    number_facets: list[NumberFacet] = []

    for attribute in attributes:
        attr_id = attribute["id"]
        attr_type = attribute["attribute_type"]

        if attr_type == "select":
            # count the amount of results for each option
            counts: dict[str, dict] = {}
            for item in items:
                for row in item_attrs_by_item.get(item["id"], []):
                    if row["attribute_id"] != attr_id or not row.get("option_id"):
                        continue
                    option_id = row["option_id"]
                    label = (row.get("attribute_options") or {}).get("value", option_id)
                    if option_id not in counts:
                        counts[option_id] = {
                            "option_id": option_id,
                            "label": label,
                            "count": 0,
                        }
                    counts[option_id]["count"] += 1

            select_facets.append(
                SelectFacet(
                    attribute_id=attr_id,
                    attribute_name=attribute["name"],
                    options=sorted(counts.values(), key=lambda opt: opt["label"]),
                )
            )

        elif attr_type == "text":
            counts: dict[str, dict] = {}
            for item in items:
                for row in item_attrs_by_item.get(item["id"], []):
                    if row["attribute_id"] != attr_id or not row.get("value_text"):
                        continue
                    value = row["value_text"]
                    if value not in counts:
                        counts[value] = {"value": value, "count": 0}
                    counts[value]["count"] += 1

            text_facets.append(
                TextFacet(
                    attribute_id=attr_id,
                    attribute_name=attribute["name"],
                    options=sorted(counts.values(), key=lambda opt: opt["value"]),
                )
            )

        elif attr_type == "number":
            # get all number values
            values = []
            for item in items:
                for row in item_attrs_by_item.get(item["id"], []):
                    if row["attribute_id"] == attr_id and row.get("value_number") is not None:
                        values.append(float(row["value_number"]))

            # create suggested min/max range
            number_facets.append(
                NumberFacet(
                    attribute_id=attr_id,
                    attribute_name=attribute["name"],
                    min_value=min(values) if values else None,
                    max_value=max(values) if values else None,
                )
            )

    return select_facets, text_facets, number_facets
