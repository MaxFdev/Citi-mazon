from unittest.mock import patch

from services.search import NumberFacet, SearchResult, SelectFacet


def _search_result(**overrides):
    defaults = {
        "query": "",
        "department_id": None,
        "active_departments": [],
        "items": [],
        "select_facets": [],
        "number_facets": [],
    }
    defaults.update(overrides)
    return SearchResult(**defaults)


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_search_page(mock_search, mock_list_departments, client):
    mock_list_departments.return_value = [
        {"id": "dept-1", "name": "Citi Merch", "department_attributes": []},
    ]
    mock_search.return_value = _search_result(
        query="hoodie",
        active_departments=[{"id": "dept-1", "name": "Citi Merch"}],
        items=[
            {
                "title": "Citi Hoodie",
                "description": "Warm",
                "price": 29.99,
                "vendor_name": "Acme",
                "departments": {"name": "Citi Merch"},
                "item_attributes": [],
            }
        ],
    )

    response = client.get("/user/?q=hoodie")

    assert response.status_code == 200
    assert b'value="hoodie"' in response.data
    assert b"Citi Hoodie" in response.data
    assert b"Citi Merch" in response.data
    mock_search.assert_called_once_with(
        query="hoodie",
        department_id=None,
        filters={},
    )


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_passes_department_and_filters(mock_search, mock_list_departments, client):
    mock_list_departments.return_value = []
    mock_search.return_value = _search_result(
        query="laptop",
        department_id="dept-2",
        select_facets=[
            SelectFacet(
                attribute_id="attr-1",
                attribute_name="Brand",
                options=[{"option_id": "opt-1", "label": "Dell", "count": 2}],
            )
        ],
        number_facets=[
            NumberFacet(
                attribute_id="attr-2",
                attribute_name="Weight",
                min_value=1.0,
                max_value=5.0,
            )
        ],
    )

    response = client.get(
        "/user/?q=laptop&department_id=dept-2&filter_attr-1=opt-1&filter_attr-2_min=1"
    )

    assert response.status_code == 200
    assert b"Brand" in response.data
    assert b"Dell (2)" in response.data
    assert b"Weight" in response.data
    mock_search.assert_called_once_with(
        query="laptop",
        department_id="dept-2",
        filters={
            "attr-1": {"option_id": "opt-1"},
            "attr-2": {"min": "1"},
        },
    )


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_shows_item_attributes(mock_search, mock_list_departments, client):
    mock_list_departments.return_value = []
    mock_search.return_value = _search_result(
        items=[
            {
                "title": "Laptop",
                "description": "",
                "price": 999.0,
                "vendor_name": "Acme",
                "departments": {"name": "Citi Computers"},
                "item_attributes": [
                    {
                        "department_attributes": {"name": "Brand"},
                        "attribute_options": {"value": "Dell"},
                    }
                ],
            }
        ],
    )

    response = client.get("/user/")

    assert response.status_code == 200
    assert b"Brand:" in response.data
    assert b"Dell" in response.data


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_no_results_message(mock_search, mock_list_departments, client):
    mock_list_departments.return_value = []
    mock_search.return_value = _search_result()

    response = client.get("/user/")

    assert response.status_code == 200
    assert b"No items found." in response.data
