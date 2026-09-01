from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.departments import get_department, list_departments
from services.errors import ValidationError
from services.items import create_item

vendor_bp = Blueprint("vendor", __name__, url_prefix="/vendor")


def _parse_attribute_values(form, department_id: str) -> dict[str, object]:
    from services.departments import list_department_attributes

    values: dict[str, object] = {}
    for attribute in list_department_attributes(department_id):
        key = f"attr_{attribute['id']}"
        if key in form:
            values[attribute["id"]] = form.get(key)
    return values


def _render_register(department_id: str | None = None, status_code: int = 200):
    selected = get_department(department_id) if department_id else None
    return (
        render_template(
            "vendor/index.html",
            departments=list_departments(),
            selected_department=selected,
            department_id=department_id,
        ),
        status_code,
    )


@vendor_bp.get("/")
def index():
    department_id = request.args.get("department_id") or None
    return _render_register(department_id)


@vendor_bp.post("/")
def register():
    department_id = (request.form.get("department_id") or "").strip()
    if not department_id:
        flash("Choose a department first.", "error")
        return _render_register(None, 400)

    vendor_name = request.form.get("vendor_name", "")
    title = request.form.get("title", "")
    description = request.form.get("description", "")
    price_raw = request.form.get("price", "").strip()

    try:
        price = float(price_raw)
    except ValueError:
        flash("Price must be a number.", "error")
        return _render_register(department_id, 400)

    try:
        create_item(
            department_id=department_id,
            vendor_name=vendor_name,
            title=title,
            description=description,
            price=price,
            attribute_values=_parse_attribute_values(request.form, department_id),
        )
    except ValidationError as exc:
        flash(str(exc), "error")
        return _render_register(department_id, 400)

    flash(f"Listed item '{title.strip()}'.", "success")
    return redirect(url_for("vendor.index", department_id=department_id))
