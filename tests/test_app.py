from unittest.mock import patch


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Hello from Citi-mazon"}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_health_supabase_missing_env(client, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)

    response = client.get("/health/supabase")
    assert response.status_code == 500
    assert response.get_json()["supabase"] == "error"


@patch("app.check_supabase_connection")
def test_health_supabase_connected(mock_check, client, monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "test-key")

    response = client.get("/health/supabase")
    assert response.status_code == 200
    assert response.get_json() == {"supabase": "connected"}
    mock_check.assert_called_once_with("https://example.supabase.co", "test-key")
