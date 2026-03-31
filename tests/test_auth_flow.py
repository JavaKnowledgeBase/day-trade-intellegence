"""Tests for the local bearer-token authentication flow."""

from fastapi.testclient import TestClient

from app.main import app


def test_login_and_current_user_flow() -> None:
    """Validate that seeded local users can log in and access the current-user endpoint with a bearer token."""
    with TestClient(app) as client:
        login_response = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin123'})
        assert login_response.status_code == 200
        token = login_response.json()['access_token']

        me_response = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
        assert me_response.status_code == 200
        assert me_response.json()['username'] == 'admin'
        assert me_response.json()['role'] == 'ADMIN'
