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
class NumberFacet:
    attribute_id: str
    attribute_name: str
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class SearchResult:
    query: str
    department_id: str | None
    active_departments: list[dict]
    items: list[dict]
    select_facets: list[SelectFacet]
    number_facets: list[NumberFacet]

# actual search

def search(
    query: str = "",
    department_id: str | None = None,
    filters: dict | None = None,
) -> SearchResult:
    filters = filters or {}
    q = query.strip()

    departments = _list_departments()
    term_matched = _departments_matching_terms(q, departments) if q else []

    items = _fetch_items(q, department_id)
    
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

    # only filter by attributes when a department is selected
    item_attrs_by_item = _load_item_attributes([item["id"] for item in items])

    # filter by attributes for selected department
    if department_id:
        attributes = _attributes_for_departments({department_id})
        items = _apply_filters(items, item_attrs_by_item, attributes, filters)
        
        # drop attribute rows for items filtered out
        item_attrs_by_item = {
            item_id: attrs
            for item_id, attrs in item_attrs_by_item.items()
            if item_id in {item["id"] for item in items}
        }
        select_facets, number_facets = _build_facets(
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
        number_facets=number_facets,
    )


def parse_filters(args) -> dict:
    """Turn query params like filter_<id>=opt into a filter spec dict."""
    filters: dict = {}

    for key, value in args.items():
        # only care about non-empty filter_* params
        if not key.startswith("filter_") or not value:
            continue

        body = key.removeprefix("filter_")
        # number range lower bound
        if body.endswith("_min"):
            attr_id = body.removesuffix("_min")
            filters.setdefault(attr_id, {})["min"] = value
        # number range upper bound
        elif body.endswith("_max"):
            attr_id = body.removesuffix("_max")
            filters.setdefault(attr_id, {})["max"] = value
        # select option id
        else:
            filters[body] = {"option_id": value}

    return filters


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


def _fetch_items(query: str, department_id: str | None) -> list[dict]:
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

    return request.execute().data


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
        .select("*, attribute_options(value)")
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
        return item_attr.get("option_id") == spec.get("option_id")

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

    # text attrs are not filterable (for now, might add to frontend)
    return True


def _build_facets(
    items: list[dict],
    item_attrs_by_item: dict[str, list[dict]],
    attributes: list[dict],
) -> tuple[list[SelectFacet], list[NumberFacet]]:
    select_facets: list[SelectFacet] = []
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

    return select_facets, number_facets
