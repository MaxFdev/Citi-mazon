from unittest.mock import patch

from werkzeug.datastructures import MultiDict

from services.errors import ValidationError


def _sample_department():
    return {
        "name": "Citi Merch",
        "description": "Branded apparel and accessories.",
        "search_terms": ["merch", "shirt", "hoodie"],
        "department_attributes": [
            {
                "name": "Size",
                "attribute_type": "select",
                "attribute_options": [
                    {"value": "M"},
                    {"value": "L"},
                ],
            },
            {
                "name": "Care",
                "attribute_type": "text",
                "attribute_options": [],
            },
        ],
    }


@patch("blueprints.site.list_departments")
def test_site_get_empty(mock_list_departments, client):
    mock_list_departments.return_value = []

    response = client.get("/site/")

    assert response.status_code == 200
    assert b"Site admin" in response.data
    assert b"No departments yet" in response.data
    assert b"Add attribute" in response.data
    assert b"Create department" in response.data
    mock_list_departments.assert_called_once()


@patch("blueprints.site.list_departments")
def test_site_get_lists_existing_departments(mock_list_departments, client):
    mock_list_departments.return_value = [_sample_department()]

    response = client.get("/site/")

    assert response.status_code == 200
    assert b"Citi Merch" in response.data
    assert b"Branded apparel and accessories." in response.data
    assert b"merch, shirt, hoodie" in response.data
    assert b"Size (select)" in response.data
    assert b"M, L" in response.data
    assert b"Care (text)" in response.data


@patch("blueprints.site.create_department")
@patch("blueprints.site.list_departments")
def test_site_create_success_redirects_with_flash(
    mock_list_departments,
    mock_create_department,
    client,
):
    mock_list_departments.return_value = []
    mock_create_department.return_value = {"name": "Citi Computers"}

    response = client.post(
        "/site/",
        data={
            "name": "Citi Computers",
            "description": "Laptops and desktops for work.",
            "search_terms": "laptop, computer, pc",
            "attr_name": "Brand",
            "attr_type": "select",
            "attr_options": "Dell, HP",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Created department &#39;Citi Computers&#39;." in response.data
    mock_create_department.assert_called_once_with(
        name="Citi Computers",
        description="Laptops and desktops for work.",
        search_terms=["laptop", "computer", "pc"],
        attributes=[{
            "name": "Brand",
            "attribute_type": "select",
            "options": ["Dell", "HP"],
        }],
    )


@patch("blueprints.site.create_department")
@patch("blueprints.site.list_departments")
def test_site_create_multiple_attribute_types(
    mock_list_departments,
    mock_create_department,
    client,
):
    mock_list_departments.return_value = []
    mock_create_department.return_value = {"name": "Citi Computers"}

    response = client.post(
        "/site/",
        data=MultiDict([
            ("name", "Citi Computers"),
            ("attr_name", "Brand"),
            ("attr_type", "select"),
            ("attr_options", "Dell, HP"),
            ("attr_name", "Weight"),
            ("attr_type", "number"),
            ("attr_options", ""),
            ("attr_name", "Notes"),
            ("attr_type", "text"),
            ("attr_options", ""),
        ]),
        follow_redirects=False,
    )

    assert response.status_code == 302
    attributes = mock_create_department.call_args.kwargs["attributes"]
    assert len(attributes) == 3
    assert attributes[0]["attribute_type"] == "select"
    assert attributes[1]["attribute_type"] == "number"
    assert attributes[2]["attribute_type"] == "text"
    assert "options" not in attributes[2]


@patch("blueprints.site.create_department")
@patch("blueprints.site.list_departments")
def test_site_create_skips_blank_attribute_rows(
    mock_list_departments,
    mock_create_department,
    client,
):
    mock_list_departments.return_value = []
    mock_create_department.return_value = {"name": "Citi Merch"}

    response = client.post(
        "/site/",
        data=MultiDict([
            ("name", "Citi Merch"),
            ("attr_name", "Size"),
            ("attr_type", "select"),
            ("attr_options", "S, M"),
            ("attr_name", ""),
            ("attr_type", "text"),
            ("attr_options", ""),
        ]),
        follow_redirects=False,
    )

    assert response.status_code == 302
    attributes = mock_create_department.call_args.kwargs["attributes"]
    assert len(attributes) == 1
    assert attributes[0]["name"] == "Size"


@patch("blueprints.site.create_department")
@patch("blueprints.site.list_departments")
def test_site_create_validation_error_shows_flash(
    mock_list_departments,
    mock_create_department,
    client,
):
    mock_list_departments.return_value = []
    mock_create_department.side_effect = ValidationError("Department name is required.")

    response = client.post(
        "/site/",
        data={"name": ""},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"Department name is required" in response.data
    mock_list_departments.assert_called_once()


@patch("blueprints.site.create_department")
@patch("blueprints.site.list_departments")
def test_site_create_requires_attributes(mock_list_departments, mock_create_department, client):
    mock_list_departments.return_value = []
    mock_create_department.side_effect = ValidationError("At least one attribute is required.")

    response = client.post(
        "/site/",
        data={
            "name": "Citi Merch",
            "attr_name": "",
            "attr_type": "",
            "attr_options": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"At least one attribute is required" in response.data


@patch("blueprints.site.create_department")
@patch("blueprints.site.list_departments")
def test_site_create_select_requires_options(mock_list_departments, mock_create_department, client):
    mock_list_departments.return_value = []
    mock_create_department.side_effect = ValidationError(
        "Select attribute 'Size' requires at least one option."
    )

    response = client.post(
        "/site/",
        data={
            "name": "Citi Merch",
            "attr_name": "Size",
            "attr_type": "select",
            "attr_options": "",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"Select attribute &#39;Size&#39; requires at least one option." in response.data


@patch("blueprints.site.list_departments")
def test_site_form_posts_to_create_route(mock_list_departments, client):
    mock_list_departments.return_value = []

    response = client.get("/site/")

    assert b'action="/site/"' in response.data
    assert b'method="post"' in response.data
