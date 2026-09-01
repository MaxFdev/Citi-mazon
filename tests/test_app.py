from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError


def test_index(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/user/")


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_supabase_missing_env(client, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    response = client.get("/health/supabase")
    assert response.status_code == 500
    assert response.get_json()["supabase"] == "error"


@patch("app.check_supabase_connection")
def test_health_supabase_connected(mock_check, client, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

    response = client.get("/health/supabase")
    assert response.status_code == 200
    assert response.get_json() == {"supabase": "connected"}
    mock_check.assert_called_once_with()


@patch("app.get_supabase")
def test_check_supabase_connection_ok(mock_get_supabase):
    from app import check_supabase_connection

    mock_get_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()

    check_supabase_connection()

    mock_get_supabase.return_value.table.assert_called_once_with("departments")


@patch("app.get_supabase")
def test_check_supabase_connection_missing_table(mock_get_supabase):
    from app import check_supabase_connection

    mock_get_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.side_effect = APIError(
        {"message": "Could not find the table", "code": "PGRST205", "hint": None, "details": None}
    )

    check_supabase_connection()


@patch("app.get_supabase")
def test_check_supabase_connection_api_error(mock_get_supabase):
    from app import check_supabase_connection

    mock_get_supabase.return_value.table.return_value.select.return_value.limit.return_value.execute.side_effect = APIError(
        {"message": "permission denied", "code": "42501", "hint": None, "details": None}
    )

    with pytest.raises(APIError):
        check_supabase_connection()
