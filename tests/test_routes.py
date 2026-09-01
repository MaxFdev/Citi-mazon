from unittest.mock import patch

from services.errors import ValidationError


def test_user_placeholder(client):
    response = client.get("/user/")
    assert response.status_code == 200
    assert b"Shop" in response.data


def test_vendor_placeholder(client):
    response = client.get("/vendor/")
    assert response.status_code == 200
    assert b"Vendor" in response.data


def test_root_redirects_to_user(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/user/")
