from unittest.mock import patch

from scripts.seed_data import (
    CITI_COMPUTERS,
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
@patch("scripts.seed_data.seed_already_applied")
def test_seed_skips_when_already_applied(mock_already_applied, mock_seed_department, capsys):
    mock_already_applied.return_value = True

    seed()

    mock_seed_department.assert_not_called()
    assert "already present" in capsys.readouterr().out


@patch("scripts.seed_data._seed_department")
@patch("scripts.seed_data.seed_already_applied")
def test_seed_creates_both_departments(mock_already_applied, mock_seed_department, capsys):
    mock_already_applied.return_value = False
    mock_seed_department.side_effect = [
        {"name": "Citi Merch"},
        {"name": "Citi Computers"},
    ]

    seed()

    assert mock_seed_department.call_args_list[0].args[0] is CITI_MERCH
    assert mock_seed_department.call_args_list[1].args[0] is CITI_COMPUTERS
    output = capsys.readouterr().out
    assert "Citi Merch" in output
    assert "Citi Computers" in output
