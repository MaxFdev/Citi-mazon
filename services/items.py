from db import get_supabase
from services.departments import list_department_attributes
from services.errors import ValidationError


def create_item(
    department_id: str,
    vendor_name: str,
    title: str,
    description: str,
    price: float,
    attribute_values: dict[str, object],
) -> dict:
    vendor_name = vendor_name.strip()
    title = title.strip()
    description = description.strip()

    if not vendor_name:
        raise ValidationError("Vendor name is required.")
    if not title:
        raise ValidationError("Title is required.")
    if price < 0:
        raise ValidationError("Price must be zero or greater.")

    attributes = list_department_attributes(department_id)
    if not attributes:
        raise ValidationError("Department has no attributes defined.")

    rows = _build_item_attribute_rows(attributes, attribute_values)

    # doing two requests to avoid setting up the RPC call for a single transaction (not a best practice)
    sb = get_supabase()
    item_response = (
        sb.table("items")
        .insert({
            "department_id": department_id,
            "vendor_name": vendor_name,
            "title": title,
            "description": description,
            "price": price,
        })
        .execute()
    )
    item = item_response.data[0]

    for row in rows:
        row["item_id"] = item["id"]

    sb.table("item_attributes").insert(rows).execute()

    return _get_item(item["id"])


def _get_item(item_id: str) -> dict:
    response = (
        get_supabase()
        .table("items")
        .select(
            "*, departments(name), "
            "item_attributes(*, department_attributes(name, attribute_type), attribute_options(value))"
        )
        .eq("id", item_id)
        .single()
        .execute()
    )
    return response.data


def _build_item_attribute_rows(
    attributes: list[dict],
    attribute_values: dict[str, object],
) -> list[dict]:
    rows: list[dict] = []

    for attribute in attributes:
        attr_id = attribute["id"]
        attr_name = attribute["name"]
        attr_type = attribute["attribute_type"]

        if attr_id not in attribute_values:
            raise ValidationError(f"Missing value for attribute '{attr_name}'.")

        raw_value = attribute_values[attr_id]
        row: dict = {"attribute_id": attr_id}

        if attr_type == "select":
            option_id = str(raw_value).strip()
            valid_option_ids = {
                option["id"] for option in attribute.get("attribute_options", [])
            }
            if option_id not in valid_option_ids:
                raise ValidationError(
                    f"Invalid option for attribute '{attr_name}'."
                )
            row["option_id"] = option_id

        elif attr_type == "text":
            value_text = str(raw_value).strip()
            if not value_text:
                raise ValidationError(f"Text attribute '{attr_name}' cannot be empty.")
            row["value_text"] = value_text

        elif attr_type == "number":
            try:
                value_number = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    f"Number attribute '{attr_name}' must be numeric."
                ) from exc
            row["value_number"] = value_number

        rows.append(row)

    if len(rows) != len(attributes):
        raise ValidationError("All department attributes must be provided.")

    return rows
