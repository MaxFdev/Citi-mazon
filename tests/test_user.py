from unittest.mock import patch

from services.search import NumberFacet, PriceFacet, SearchResult, SelectFacet, TextFacet


def _search_result(**overrides):
    defaults = {
        "query": "",
        "department_id": None,
        "active_departments": [],
        "items": [],
        "select_facets": [],
        "text_facets": [],
        "number_facets": [],
        "price_facet": PriceFacet(),
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
        price_facet=PriceFacet(min_value=29.99, max_value=29.99),
    )

    response = client.get("/user/?q=hoodie")

    assert response.status_code == 200
    assert b'value="hoodie"' in response.data
    assert b"Citi Hoodie" in response.data
    assert b"Citi Merch" in response.data
    assert b"Price" in response.data
    mock_search.assert_called_once_with(
        query="hoodie",
        department_id=None,
        filters={},
        price_filter={},
    )


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_auto_selects_single_department(mock_search, mock_list_departments, client):
    mock_list_departments.return_value = []
    mock_search.return_value = _search_result(
        query="hoodie",
        items=[
            {
                "department_id": "dept-1",
                "title": "Citi Hoodie",
                "price": 29.99,
            }
        ],
    )

    response = client.get("/user/?q=hoodie", follow_redirects=False)

    assert response.status_code == 302
    assert "department_id=dept-1" in response.location


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_passes_department_and_filters(mock_search, mock_list_departments, client):
    mock_list_departments.return_value = []
    mock_search.return_value = _search_result(
        query="laptop",
        department_id="dept-2",
        price_min="100",
        select_facets=[
            SelectFacet(
                attribute_id="attr-1",
                attribute_name="Brand",
                options=[{"option_id": "opt-1", "label": "Dell", "count": 2}],
            )
        ],
        text_facets=[
            TextFacet(
                attribute_id="attr-3",
                attribute_name="Room",
                options=[{"value": "Office", "count": 1}],
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
        price_facet=PriceFacet(min_value=100.0, max_value=2000.0),
    )

    response = client.get(
        "/user/?q=laptop&department_id=dept-2&filter_attr-1=opt-1"
        "&filter_attr-2_min=1&price_min=100"
    )

    assert response.status_code == 200
    assert b"Brand" in response.data
    assert b"Dell (2)" in response.data
    assert b"Room" in response.data
    assert b"Weight" in response.data
    assert b"Clear all filters" in response.data
    mock_search.assert_called_once_with(
        query="laptop",
        department_id="dept-2",
        filters={
            "attr-1": {"option_id": "opt-1"},
            "attr-2": {"min": "1"},
        },
        price_filter={"min": "100"},
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
                        "department_attributes": {"name": "Brand", "attribute_type": "select"},
                        "attribute_options": {"value": "Dell"},
                    },
                    {
                        "department_attributes": {"name": "Care", "attribute_type": "text"},
                        "value_text": "Handle with care",
                    },
                ],
            }
        ],
    )

    response = client.get("/user/")

    assert response.status_code == 200
    assert b"Brand:" in response.data
    assert b"Dell" in response.data
    assert b"Hide text details" in response.data
    assert b"item-attr-text" in response.data


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_no_results_message(mock_search, mock_list_departments, client):
    mock_list_departments.return_value = []
    mock_search.return_value = _search_result()

    response = client.get("/user/")

    assert response.status_code == 200
    assert b"No items found." in response.data
