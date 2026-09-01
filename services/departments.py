from db import get_supabase
from services.errors import ValidationError

ATTRIBUTE_TYPES = frozenset({"select", "text", "number"})

DEPARTMENT_SELECT = "*, department_attributes(*, attribute_options(*))"


def parse_search_terms(raw: str) -> list[str]:
    return [term.strip() for term in raw.split(",") if term.strip()]


def list_departments() -> list[dict]:
    response = (
        get_supabase()
        .table("departments")
        .select(DEPARTMENT_SELECT)
        .order("name")
        .execute()
    )
    return response.data


def get_department(department_id: str) -> dict | None:
    response = (
        get_supabase()
        .table("departments")
        .select(DEPARTMENT_SELECT)
        .eq("id", department_id)
        .maybe_single()
        .execute()
    )
    return response.data


def list_department_attributes(department_id: str) -> list[dict]:
    response = (
        get_supabase()
        .table("department_attributes")
        .select("*, attribute_options(*)")
        .eq("department_id", department_id)
        .order("name")
        .execute()
    )
    return response.data


def _validate_attribute_input(attribute: dict) -> None:
    name = (attribute.get("name") or "").strip()
    attribute_type = attribute.get("attribute_type")

    if not name:
        raise ValidationError("Attribute name is required.")

    if attribute_type not in ATTRIBUTE_TYPES:
        raise ValidationError(f"Invalid attribute type: {attribute_type!r}.")

    if attribute_type == "select":
        options = [opt.strip() for opt in attribute.get("options", []) if opt.strip()]
        if not options:
            raise ValidationError(f"Select attribute '{name}' requires at least one option.")


def create_department(
    name: str,
    description: str,
    search_terms: list[str],
    attributes: list[dict],
) -> dict:
    name = name.strip()
    if not name:
        raise ValidationError("Department name is required.")

    if not attributes:
        raise ValidationError("At least one attribute is required.")

    for attribute in attributes:
        _validate_attribute_input(attribute)

    sb = get_supabase()

    department_response = (
        sb.table("departments")
        .insert({
            "name": name,
            "description": description.strip(),
            "search_terms": search_terms,
        })
        .execute()
    )
    department = department_response.data[0]

    for attribute in attributes:
        attr_response = (
            sb.table("department_attributes")
            .insert({
                "department_id": department["id"],
                "name": attribute["name"].strip(),
                "attribute_type": attribute["attribute_type"],
            })
            .execute()
        )
        created_attribute = attr_response.data[0]

        if attribute["attribute_type"] == "select":
            option_rows = [
                {
                    "attribute_id": created_attribute["id"],
                    "value": option.strip(),
                }
                for option in attribute["options"]
                if option.strip()
            ]
            sb.table("attribute_options").insert(option_rows).execute()

    created = get_department(department["id"])
    if created is None:
        raise ValidationError("Department was created but could not be loaded.")
    return created
