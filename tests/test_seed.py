from unittest.mock import patch

from scripts.seed_data import (
    CITI_COMPUTERS,
    CITI_HOME,
    CITI_MERCH,
    _attribute_values,
    seed,
    seed_already_applied,
)


def _department_fixture():
    return {
        "id": "dept-1",
        "name": "Citi Merch",
        "department_attributes": [
            {
                "id": "attr-size",
                "name": "Size",
                "attribute_type": "select",
                "attribute_options": [
                    {"id": "opt-m", "value": "M"},
                ],
            },
            {
                "id": "attr-care",
                "name": "Care",
                "attribute_type": "text",
                "attribute_options": [],
            },
        ],
    }


def test_seed_already_applied_true():
    with patch("scripts.seed_data.list_departments") as mock_list:
        mock_list.return_value = [
            {"name": "Citi Merch"},
            {"name": "Citi Computers"},
            {"name": "Citi Home"},
        ]
        assert seed_already_applied() is True


def test_seed_already_applied_false():
    with patch("scripts.seed_data.list_departments") as mock_list:
        mock_list.return_value = [{"name": "Citi Merch"}]
        assert seed_already_applied() is False


def test_attribute_values_maps_select_text_and_number():
    department = _department_fixture()

    values = _attribute_values(
        department,
        {
            "Size": ("select", "M"),
            "Care": ("text", "Machine wash cold"),
        },
    )

    assert values == {
        "attr-size": "opt-m",
        "attr-care": "Machine wash cold",
    }


@patch("scripts.seed_data._seed_department")
@patch("scripts.seed_data.missing_department_specs")
def test_seed_skips_when_already_applied(mock_missing, mock_seed_department, capsys):
    mock_missing.return_value = []

    seed()

    mock_seed_department.assert_not_called()
    assert "already present" in capsys.readouterr().out


@patch("scripts.seed_data._seed_department")
@patch("scripts.seed_data.missing_department_specs")
def test_seed_creates_all_departments(mock_missing, mock_seed_department, capsys):
    mock_missing.return_value = [CITI_MERCH, CITI_COMPUTERS, CITI_HOME]
    mock_seed_department.side_effect = [
        {"name": "Citi Merch"},
        {"name": "Citi Computers"},
        {"name": "Citi Home"},
    ]

    seed()

    assert mock_seed_department.call_args_list[0].args[0] is CITI_MERCH
    assert mock_seed_department.call_args_list[1].args[0] is CITI_COMPUTERS
    assert mock_seed_department.call_args_list[2].args[0] is CITI_HOME
    output = capsys.readouterr().out
    assert "Citi Merch" in output
    assert "Citi Computers" in output
    assert "Citi Home" in output


@patch("scripts.seed_data._seed_department")
@patch("scripts.seed_data.list_departments")
def test_seed_creates_only_missing_departments(mock_list, mock_seed_department, capsys):
    mock_list.return_value = [
        {"name": "Citi Merch"},
        {"name": "Citi Computers"},
    ]
    mock_seed_department.return_value = {"name": "Citi Home"}

    seed()

    mock_seed_department.assert_called_once_with(CITI_HOME)
    output = capsys.readouterr().out
    assert "Skipping Citi Merch" in output
    assert "Skipping Citi Computers" in output
    assert "Created Citi Home" in output
