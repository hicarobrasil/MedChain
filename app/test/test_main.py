import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.test.conftest import client # Import client fixture from conftest

def test_app_creation(client):
    """
    Test that the app can be created successfully.
    """
    assert client is not None
    assert app.title == "MediVault API"

def test_routes_included(client):
    """
    Verify that routes (like /api/v1/doctors) are included.
    """
    # The client fixture uses the app with overridden dependencies
    # We just need to check if the route exists.
    # We can try a simple request to a known route or check app.routes
    
    # Check if the route exists by trying to access it (might return 401/403 or something else, 
    # but 404 would mean it's not registered)
    response = client.get("/api/v1/doctors/")
    
    # 401 or 403 or 200 depending on auth. 
    # Just checking it's not a 404 is good enough to verify it's included.
    assert response.status_code != 404
