from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.departments import create_department, list_departments, parse_search_terms
from services.errors import ValidationError

site_bp = Blueprint("site", __name__, url_prefix="/site")


def _parse_attributes_from_form(form) -> list[dict]:
    names = form.getlist("attr_name")
    types = form.getlist("attr_type")
    options = form.getlist("attr_options")
    attributes = []

    for name, attribute_type, options_raw in zip(names, types, options):
        name = (name or "").strip()
        if not name:
            continue

        attribute: dict = {
            "name": name,
            "attribute_type": attribute_type,
        }

        if attribute_type == "select":
            attribute["options"] = parse_search_terms(options_raw or "")

        attributes.append(attribute)

    return attributes


@site_bp.get("/")
def index():
    return render_template("site/index.html", departments=list_departments())


@site_bp.post("/")
def create():
    try:
        department = create_department(
            name=request.form.get("name", ""),
            description=request.form.get("description", ""),
            search_terms=parse_search_terms(request.form.get("search_terms", "")),
            attributes=_parse_attributes_from_form(request.form),
        )
    except ValidationError as exc:
        flash(str(exc), "error")
        return render_template(
            "site/index.html",
            departments=list_departments(),
        ), 400

    flash(f"Created department '{department['name']}'.", "success")
    return redirect(url_for("site.index"))
