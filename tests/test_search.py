from unittest.mock import MagicMock, patch

from services.search import parse_filters, search


def test_parse_filters():
    args = {
        "filter_attr-1": "opt-1",
        "filter_attr-2_min": "10",
        "filter_attr-2_max": "50",
        "q": "laptop",
    }
    assert parse_filters(args) == {
        "attr-1": {"option_id": "opt-1"},
        "attr-2": {"min": "10", "max": "50"},
    }


@patch("services.search.get_supabase")
def test_search_merges_term_and_item_departments(mock_get_supabase):
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb

    departments = [
        {"id": "dept-1", "name": "Electronics", "search_terms": ["laptop"]},
        {"id": "dept-2", "name": "Books", "search_terms": ["reading"]},
    ]
    items = [
        {
            "id": "item-1",
            "department_id": "dept-2",
            "vendor_name": "Acme",
            "title": "Laptop Guide",
            "description": "",
            "price": 10,
            "departments": {"name": "Books"},
        }
    ]
    attributes = [
        {
            "id": "attr-1",
            "department_id": "dept-1",
            "name": "Brand",
            "attribute_type": "select",
            "attribute_options": [{"id": "opt-1", "value": "Dell"}],
        }
    ]
    item_attributes = [
        {
            "item_id": "item-1",
            "attribute_id": "attr-1",
            "option_id": "opt-1",
            "value_number": None,
            "attribute_options": {"value": "Dell"},
        }
    ]

    def table(name):
        mock = MagicMock()
        if name == "departments":
            mock.select.return_value.order.return_value.execute.return_value.data = departments
        elif name == "items":
            mock.select.return_value.limit.return_value.or_.return_value.execute.return_value.data = items
            mock.select.return_value.limit.return_value.execute.return_value.data = items
        elif name == "department_attributes":
            mock.select.return_value.in_.return_value.order.return_value.execute.return_value.data = attributes
        elif name == "item_attributes":
            mock.select.return_value.in_.return_value.execute.return_value.data = item_attributes
        return mock

    mock_sb.table.side_effect = table

    result = search(query="laptop")

    assert len(result.items) == 1
    assert {dept["id"] for dept in result.active_departments} == {"dept-1", "dept-2"}
    assert result.select_facets == []
    assert result.number_facets == []


@patch("services.search.get_supabase")
def test_search_ignores_filters_without_department(mock_get_supabase):
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb

    departments = [{"id": "dept-1", "name": "Electronics", "search_terms": []}]
    items = [
        {
            "id": "item-1",
            "department_id": "dept-1",
            "vendor_name": "Acme",
            "title": "Laptop",
            "description": "",
            "price": 10,
            "departments": {"name": "Electronics"},
        },
        {
            "id": "item-2",
            "department_id": "dept-1",
            "vendor_name": "Acme",
            "title": "Desktop",
            "description": "",
            "price": 12,
            "departments": {"name": "Electronics"},
        },
    ]
    item_attributes = [
        {
            "item_id": "item-1",
            "attribute_id": "attr-1",
            "option_id": "opt-1",
            "attribute_options": {"value": "Dell"},
        },
        {
            "item_id": "item-2",
            "attribute_id": "attr-1",
            "option_id": "opt-2",
            "attribute_options": {"value": "HP"},
        },
    ]

    def table(name):
        mock = MagicMock()
        if name == "departments":
            mock.select.return_value.order.return_value.execute.return_value.data = departments
        elif name == "items":
            mock.select.return_value.limit.return_value.execute.return_value.data = items
        elif name == "item_attributes":
            mock.select.return_value.in_.return_value.execute.return_value.data = item_attributes
        return mock

    mock_sb.table.side_effect = table

    result = search(filters={"attr-1": {"option_id": "opt-1"}})

    assert len(result.items) == 2


@patch("services.search.get_supabase")
def test_search_applies_select_filter_when_department_selected(mock_get_supabase):
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb

    departments = [{"id": "dept-1", "name": "Electronics", "search_terms": []}]
    items = [
        {
            "id": "item-1",
            "department_id": "dept-1",
            "vendor_name": "Acme",
            "title": "Laptop",
            "description": "",
            "price": 10,
            "departments": {"name": "Electronics"},
        },
        {
            "id": "item-2",
            "department_id": "dept-1",
            "vendor_name": "Acme",
            "title": "Desktop",
            "description": "",
            "price": 12,
            "departments": {"name": "Electronics"},
        },
    ]
    attributes = [
        {
            "id": "attr-1",
            "department_id": "dept-1",
            "name": "Brand",
            "attribute_type": "select",
            "attribute_options": [
                {"id": "opt-1", "value": "Dell"},
                {"id": "opt-2", "value": "HP"},
            ],
        }
    ]
    item_attributes = [
        {
            "item_id": "item-1",
            "attribute_id": "attr-1",
            "option_id": "opt-1",
            "attribute_options": {"value": "Dell"},
        },
        {
            "item_id": "item-2",
            "attribute_id": "attr-1",
            "option_id": "opt-2",
            "attribute_options": {"value": "HP"},
        },
    ]

    def table(name):
        mock = MagicMock()
        if name == "departments":
            mock.select.return_value.order.return_value.execute.return_value.data = departments
        elif name == "items":
            mock.select.return_value.limit.return_value.eq.return_value.execute.return_value.data = items
        elif name == "department_attributes":
            mock.select.return_value.in_.return_value.order.return_value.execute.return_value.data = attributes
        elif name == "item_attributes":
            mock.select.return_value.in_.return_value.execute.return_value.data = item_attributes
        return mock

    mock_sb.table.side_effect = table

    result = search(
        department_id="dept-1",
        filters={"attr-1": {"option_id": "opt-1"}},
    )

    assert len(result.items) == 1
    assert result.items[0]["id"] == "item-1"
    assert result.select_facets[0].options == [
        {"option_id": "opt-1", "label": "Dell", "count": 1},
    ]


@patch("services.search.get_supabase")
def test_search_builds_facets_when_department_selected(mock_get_supabase):
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb

    departments = [
        {"id": "dept-1", "name": "Electronics", "search_terms": ["laptop"]},
    ]
    items = [
        {
            "id": "item-1",
            "department_id": "dept-1",
            "vendor_name": "Acme",
            "title": "Laptop",
            "description": "",
            "price": 10,
            "departments": {"name": "Electronics"},
        }
    ]
    attributes = [
        {
            "id": "attr-1",
            "department_id": "dept-1",
            "name": "Brand",
            "attribute_type": "select",
            "attribute_options": [{"id": "opt-1", "value": "Dell"}],
        }
    ]
    item_attributes = [
        {
            "item_id": "item-1",
            "attribute_id": "attr-1",
            "option_id": "opt-1",
            "attribute_options": {"value": "Dell"},
        }
    ]

    def table(name):
        mock = MagicMock()
        if name == "departments":
            mock.select.return_value.order.return_value.execute.return_value.data = departments
        elif name == "items":
            items_mock = MagicMock()
            items_mock.select.return_value.limit.return_value.execute.return_value.data = items
            items_mock.select.return_value.limit.return_value.or_.return_value.execute.return_value.data = items
            items_mock.select.return_value.limit.return_value.eq.return_value.execute.return_value.data = items
            items_mock.select.return_value.limit.return_value.or_.return_value.eq.return_value.execute.return_value.data = items
            mock = items_mock
        elif name == "department_attributes":
            mock.select.return_value.in_.return_value.order.return_value.execute.return_value.data = attributes
        elif name == "item_attributes":
            mock.select.return_value.in_.return_value.execute.return_value.data = item_attributes
        return mock

    mock_sb.table.side_effect = table

    result = search(query="laptop", department_id="dept-1")

    assert result.select_facets[0].options[0]["label"] == "Dell"
