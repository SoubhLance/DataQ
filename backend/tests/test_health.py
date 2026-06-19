import pytest

@pytest.mark.integration
def test_health_endpoints(client):
    """
    Verify GET /, GET /docs, GET /openapi.json return 200.
    """
    # Test Root
    res_root = client.get("/")
    assert res_root.status_code == 200
    data = res_root.json()
    assert data["status"] == "healthy"
    assert "version" in data
    
    # Test Docs
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200
    
    # Test OpenAPI
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
