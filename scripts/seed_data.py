"""
Citi-themed demo seed data loaded via supabase-py (not SQL).

Run: uv run python scripts/seed_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from services.departments import create_department, list_departments
from services.items import create_item

DEPARTMENT_NAMES = frozenset({"Citi Merch", "Citi Computers"})

CITI_MERCH = {
    "name": "Citi Merch",
    "description": "Branded apparel and accessories for Citi fans.",
    "search_terms": ["merch", "shirt", "hoodie", "cap", "polo", "citi gear"],
    "attributes": [
        {
            "name": "Size",
            "attribute_type": "select",
            "options": ["S", "M", "L", "XL"],
        },
        {
            "name": "Color",
            "attribute_type": "select",
            "options": ["Citi Blue", "White", "Navy"],
        },
        {
            "name": "Care",
            "attribute_type": "text",
        },
    ],
    "items": [
        {
            "vendor_name": "Citi Store",
            "title": "Citi Logo Polo",
            "description": "Classic polo with embroidered Citi logo.",
            "price": 29.99,
            "attributes": {
                "Size": ("select", "M"),
                "Color": ("select", "Citi Blue"),
                "Care": ("text", "Machine wash cold"),
            },
        },
        {
            "vendor_name": "Citi Store",
            "title": "Citi Hoodie",
            "description": "Soft fleece hoodie in Citi blue.",
            "price": 49.99,
            "attributes": {
                "Size": ("select", "L"),
                "Color": ("select", "Navy"),
                "Care": ("text", "Do not bleach"),
            },
        },
        {
            "vendor_name": "Citi Store",
            "title": "Citi Cap",
            "description": "Adjustable cap with Citi wordmark.",
            "price": 19.99,
            "attributes": {
                "Size": ("select", "S"),
                "Color": ("select", "White"),
                "Care": ("text", "Spot clean only"),
            },
        },
    ],
}

CITI_COMPUTERS = {
    "name": "Citi Computers",
    "description": "Laptops and desktops configured for everyday work.",
    "search_terms": ["laptop", "computer", "pc", "desktop", "citi tech"],
    "attributes": [
        {
            "name": "Brand",
            "attribute_type": "select",
            "options": ["Dell", "HP", "Lenovo"],
        },
        {
            "name": "RAM",
            "attribute_type": "select",
            "options": ["8GB", "16GB", "32GB"],
        },
        {
            "name": "Weight",
            "attribute_type": "number",
        },
    ],
    "items": [
        {
            "vendor_name": "Citi Tech Partners",
            "title": "Citi Pro Laptop 15",
            "description": "15-inch laptop for daily office work.",
            "price": 1299.00,
            "attributes": {
                "Brand": ("select", "Dell"),
                "RAM": ("select", "16GB"),
                "Weight": ("number", 3.5),
            },
        },
        {
            "vendor_name": "Citi Tech Partners",
            "title": "Citi Travel Laptop 13",
            "description": "Lightweight 13-inch laptop for travel.",
            "price": 999.00,
            "attributes": {
                "Brand": ("select", "HP"),
                "RAM": ("select", "8GB"),
                "Weight": ("number", 2.8),
            },
        },
        {
            "vendor_name": "Citi Tech Partners",
            "title": "Citi Power Desktop",
            "description": "Desktop workstation with room to upgrade.",
            "price": 1599.00,
            "attributes": {
                "Brand": ("select", "Lenovo"),
                "RAM": ("select", "32GB"),
                "Weight": ("number", 15.0),
            },
        },
    ],
}


def seed_already_applied() -> bool:
    existing = {department["name"] for department in list_departments()}
    return DEPARTMENT_NAMES.issubset(existing)


def _attribute_id(department: dict, attribute_name: str) -> str:
    for attribute in department["department_attributes"]:
        if attribute["name"] == attribute_name:
            return attribute["id"]
    raise ValueError(f"Attribute '{attribute_name}' not found on {department['name']}")


def _option_id(department: dict, attribute_name: str, option_value: str) -> str:
    for attribute in department["department_attributes"]:
        if attribute["name"] != attribute_name:
            continue
        for option in attribute.get("attribute_options", []):
            if option["value"] == option_value:
                return option["id"]
    raise ValueError(
        f"Option '{option_value}' not found for attribute '{attribute_name}'"
    )


def _attribute_values(department: dict, item_attributes: dict) -> dict[str, object]:
    values: dict[str, object] = {}

    for attribute_name, (attribute_type, raw_value) in item_attributes.items():
        attribute_id = _attribute_id(department, attribute_name)

        if attribute_type == "select":
            values[attribute_id] = _option_id(department, attribute_name, str(raw_value))
        elif attribute_type == "text":
            values[attribute_id] = raw_value
        elif attribute_type == "number":
            values[attribute_id] = raw_value
        else:
            raise ValueError(f"Unsupported attribute type: {attribute_type}")

    return values


def _seed_department(department_spec: dict) -> dict:
    department = create_department(
        name=department_spec["name"],
        description=department_spec["description"],
        search_terms=department_spec["search_terms"],
        attributes=department_spec["attributes"],
    )

    for item_spec in department_spec["items"]:
        create_item(
            department_id=department["id"],
            vendor_name=item_spec["vendor_name"],
            title=item_spec["title"],
            description=item_spec["description"],
            price=item_spec["price"],
            attribute_values=_attribute_values(department, item_spec["attributes"]),
        )

    return department


def seed() -> None:
    if seed_already_applied():
        print("Seed data already present. Skipping.")
        return

    merch = _seed_department(CITI_MERCH)
    computers = _seed_department(CITI_COMPUTERS)

    print(f"Created {merch['name']} with {len(CITI_MERCH['items'])} items.")
    print(f"Created {computers['name']} with {len(CITI_COMPUTERS['items'])} items.")


def main() -> None:
    seed()


if __name__ == "__main__":
    main()
