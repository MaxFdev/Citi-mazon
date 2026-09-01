from unittest.mock import patch

from werkzeug.datastructures import MultiDict

from services.errors import ValidationError


def _sample_department():
    return {
        "id": "dept-1",
        "name": "Citi Merch",
        "description": "Branded apparel.",
        "search_terms": ["merch"],
        "department_attributes": [
            {
                "id": "attr-1",
                "name": "Size",
                "attribute_type": "select",
                "attribute_options": [
                    {"id": "opt-1", "value": "M"},
                    {"id": "opt-2", "value": "L"},
                ],
            },
            {
                "id": "attr-2",
                "name": "Care",
                "attribute_type": "text",
                "attribute_options": [],
            },
        ],
    }


@patch("blueprints.vendor.list_departments")
def test_vendor_get_without_department(mock_list_departments, client):
    mock_list_departments.return_value = [_sample_department()]

    response = client.get("/vendor/")

    assert response.status_code == 200
    assert b"Choose department" in response.data
    assert b"Citi Merch" in response.data
    assert b"Pick a department" in response.data
    assert b"List item" not in response.data


@patch("blueprints.vendor.get_department")
@patch("blueprints.vendor.list_departments")
def test_vendor_get_with_department_shows_form(
    mock_list_departments,
    mock_get_department,
    client,
):
    department = _sample_department()
    mock_list_departments.return_value = [department]
    mock_get_department.return_value = department

    response = client.get("/vendor/?department_id=dept-1")

    assert response.status_code == 200
    assert b"New item in Citi Merch" in response.data
    assert b'name="attr_attr-1"' in response.data
    assert b'name="attr_attr-2"' in response.data
    assert b"List item" in response.data


@patch("services.departments.list_department_attributes")
@patch("blueprints.vendor.create_item")
@patch("blueprints.vendor.get_department")
@patch("blueprints.vendor.list_departments")
def test_vendor_register_success(
    mock_list_departments,
    mock_get_department,
    mock_create_item,
    mock_list_attrs,
    client,
):
    department = _sample_department()
    mock_list_departments.return_value = [department]
    mock_get_department.return_value = department
    mock_list_attrs.return_value = department["department_attributes"]
    mock_create_item.return_value = {"title": "Hoodie"}

    response = client.post(
        "/vendor/",
        data={
            "department_id": "dept-1",
            "vendor_name": "Acme",
            "title": "Hoodie",
            "description": "Warm hoodie",
            "price": "29.99",
            "attr_attr-1": "opt-1",
            "attr_attr-2": "Machine wash",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Listed item &#39;Hoodie&#39;." in response.data
    mock_create_item.assert_called_once_with(
        department_id="dept-1",
        vendor_name="Acme",
        title="Hoodie",
        description="Warm hoodie",
        price=29.99,
        attribute_values={"attr-1": "opt-1", "attr-2": "Machine wash"},
    )


@patch("services.departments.list_department_attributes")
@patch("blueprints.vendor.create_item")
@patch("blueprints.vendor.get_department")
@patch("blueprints.vendor.list_departments")
def test_vendor_register_validation_error(
    mock_list_departments,
    mock_get_department,
    mock_create_item,
    mock_list_attrs,
    client,
):
    department = _sample_department()
    mock_list_departments.return_value = [department]
    mock_get_department.return_value = department
    mock_list_attrs.return_value = department["department_attributes"]
    mock_create_item.side_effect = ValidationError("Title is required.")

    response = client.post(
        "/vendor/",
        data=MultiDict([
            ("department_id", "dept-1"),
            ("vendor_name", "Acme"),
            ("title", ""),
            ("price", "10"),
            ("attr_attr-1", "opt-1"),
            ("attr_attr-2", "Machine wash"),
        ]),
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"Title is required." in response.data


@patch("blueprints.vendor.get_department")
@patch("blueprints.vendor.list_departments")
def test_vendor_register_invalid_price(
    mock_list_departments,
    mock_get_department,
    client,
):
    department = _sample_department()
    mock_list_departments.return_value = [department]
    mock_get_department.return_value = department

    response = client.post(
        "/vendor/",
        data={
            "department_id": "dept-1",
            "vendor_name": "Acme",
            "title": "Hoodie",
            "price": "not-a-number",
            "attr_attr-1": "opt-1",
            "attr_attr-2": "Machine wash",
        },
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"Price must be a number." in response.data


@patch("blueprints.vendor.list_departments")
def test_vendor_register_without_department(mock_list_departments, client):
    mock_list_departments.return_value = []

    response = client.post(
        "/vendor/",
        data={"title": "Hoodie"},
        follow_redirects=False,
    )

    assert response.status_code == 400
    assert b"Choose a department first." in response.data
