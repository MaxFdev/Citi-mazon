from unittest.mock import MagicMock, patch

import pytest

from services.departments import create_department, parse_search_terms
from services.errors import ValidationError


def test_parse_search_terms():
    assert parse_search_terms("laptop, computer,  pc ") == ["laptop", "computer", "pc"]


def test_create_department_requires_name():
    with pytest.raises(ValidationError, match="name"):
        create_department("", "desc", [], [{"name": "Brand", "attribute_type": "select", "options": ["A"]}])


def test_create_department_select_requires_options():
    with pytest.raises(ValidationError, match="option"):
        create_department("Electronics", "desc", [], [{"name": "Brand", "attribute_type": "select", "options": []}])


@patch("services.departments.get_department")
@patch("services.departments.get_supabase")
def test_create_department_inserts_rows(mock_get_supabase, mock_get_department):
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb

    dept_insert = MagicMock()
    dept_insert.execute.return_value.data = [{"id": "dept-1", "name": "Electronics"}]

    attr_insert = MagicMock()
    attr_insert.execute.return_value.data = [{"id": "attr-1"}]

    options_insert = MagicMock()
    options_insert.execute.return_value = MagicMock()

    options_table = MagicMock(insert=MagicMock(return_value=options_insert))

    mock_sb.table.side_effect = lambda name: {
        "departments": MagicMock(insert=MagicMock(return_value=dept_insert)),
        "department_attributes": MagicMock(insert=MagicMock(return_value=attr_insert)),
        "attribute_options": options_table,
    }[name]

    mock_get_department.return_value = {
        "id": "dept-1",
        "name": "Electronics",
        "department_attributes": [],
    }

    result = create_department(
        "Electronics",
        "Gadgets",
        ["laptop"],
        [{"name": "Brand", "attribute_type": "select", "options": ["Dell", "HP"]}],
    )

    assert result["id"] == "dept-1"
    options_table.insert.assert_called_once()
