from unittest.mock import patch

from services.search import SearchResult

from services.errors import ValidationError


@patch("blueprints.user.list_departments")
@patch("blueprints.user.search")
def test_user_route(mock_search, mock_list_departments, client):
    from services.search import SearchResult

    mock_list_departments.return_value = []
    mock_search.return_value = SearchResult(
        query="",
        department_id=None,
        active_departments=[],
        items=[],
        select_facets=[],
        number_facets=[],
    )

    response = client.get("/user/")
    assert response.status_code == 200
    assert b"Shop" in response.data


@patch("blueprints.vendor.list_departments")
def test_vendor_route(mock_list_departments, client):
    mock_list_departments.return_value = []

    response = client.get("/vendor/")
    assert response.status_code == 200
    assert b"Vendor" in response.data


def test_root_redirects_to_user(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/user/")
