"""Tests for root, readiness, admin status, and console endpoints."""

from fastapi.testclient import TestClient

from app.main import app


def test_root_health_readiness_and_console_endpoints() -> None:
    """Validate that root, health, readiness, and console endpoints respond successfully."""
    with TestClient(app) as client:
        root_response = client.get('/api/v1/')
        health_response = client.get('/api/v1/health')
        ready_response = client.get('/api/v1/ready')
        console_response = client.get('/console')
        assert root_response.status_code == 200
        assert health_response.status_code == 200
        assert ready_response.status_code == 200
        assert console_response.status_code == 200
        assert 'docs' in root_response.json()
        assert 'ready' in ready_response.json()
        assert 'Operator Console' in console_response.text


def test_admin_system_status_requires_admin_key() -> None:
    """Validate that the admin system-status endpoint is protected and works with the admin key."""
    with TestClient(app) as client:
        unauthorized = client.get('/api/v1/admin/system/status')
        authorized = client.get('/api/v1/admin/system/status', headers={'X-API-Key': 'admin-local-key'})
        assert unauthorized.status_code == 401
        assert authorized.status_code == 200
        assert 'database' in authorized.json()
