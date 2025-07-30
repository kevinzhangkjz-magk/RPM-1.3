from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "RPM Solar Performance API is running"}


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_sites_endpoint():
    """Test the sites endpoint (should require authentication)"""
    response = client.get("/api/sites/")
    # Should return 401 since authentication is required
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
