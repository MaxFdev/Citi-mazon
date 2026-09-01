from unittest.mock import MagicMock, patch

import pytest

from services.errors import ValidationError
from services.items import create_item


@patch("services.items._get_item")
@patch("services.items.get_supabase")
@patch("services.items.list_department_attributes")
def test_create_item_validates_all_attributes(mock_list_attrs, mock_get_supabase, mock_get_item):
    mock_list_attrs.return_value = [
        {
            "id": "attr-1",
            "name": "Brand",
            "attribute_type": "select",
            "attribute_options": [{"id": "opt-1", "value": "Dell"}],
        },
        {
            "id": "attr-2",
            "name": "Weight",
            "attribute_type": "number",
            "attribute_options": [],
        },
    ]

    with pytest.raises(ValidationError, match="Weight"):
        create_item(
            "dept-1",
            "Acme",
            "Laptop",
            "A nice laptop",
            999.99,
            {"attr-1": "opt-1"},
        )


@patch("services.items._get_item")
@patch("services.items.get_supabase")
@patch("services.items.list_department_attributes")
def test_create_item_inserts_rows(mock_list_attrs, mock_get_supabase, mock_get_item):
    mock_list_attrs.return_value = [
        {
            "id": "attr-1",
            "name": "Notes",
            "attribute_type": "text",
            "attribute_options": [],
        },
    ]

    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb

    item_insert = MagicMock()
    item_insert.execute.return_value.data = [{"id": "item-1"}]
    mock_sb.table.return_value.insert.return_value = item_insert

    mock_get_item.return_value = {"id": "item-1", "title": "Laptop"}

    result = create_item(
        "dept-1",
        "Acme",
        "Laptop",
        "A nice laptop",
        999.99,
        {"attr-1": "Like new"},
    )

    assert result["id"] == "item-1"
    assert mock_sb.table.return_value.insert.call_count == 2
