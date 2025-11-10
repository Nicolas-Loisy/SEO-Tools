"""Tests for main application."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SEO SaaS Tool"
    assert data["status"] == "healthy"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "api" in data
