import os
import pytest
import uuid
from datetime import datetime, timedelta
from app.config.settings import settings
from app.utils.dataframe_cache import cache_manager
from app.utils.cache_cleanup import CacheCleanupThread

@pytest.mark.integration
def test_invalid_session_uuid_format(client):
    """Verify that a malformed session ID (not a valid UUID) returns 400."""
    response = client.get("/api/v1/inspect/not-a-valid-uuid")
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_FAILED"
    assert "Invalid session ID format" in data["message"]

@pytest.mark.integration
def test_nonexistent_session_uuid(client):
    """Verify that a valid but nonexistent session ID returns 404."""
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/inspect/{random_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "SESSION_NOT_FOUND"

@pytest.mark.integration
def test_deleted_session(client, create_temp_file):
    """Verify that a deleted session returns 404."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Verify works
    inspect_res = client.get(f"/api/v1/inspect/{session_id}")
    assert inspect_res.status_code == 200
    
    # Delete session
    delete_res = client.delete(f"/api/v1/upload/{session_id}")
    assert delete_res.status_code == 200
    
    # Request again - should return 404
    inspect_res2 = client.get(f"/api/v1/inspect/{session_id}")
    assert inspect_res2.status_code == 404

@pytest.mark.integration
def test_expired_session(client, create_temp_file):
    """Verify that an expired session is cleaned up and subsequently returns 404."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Manually modify last_accessed time to be older than the timeout
    session_state = cache_manager.peek(session_id)
    assert session_state is not None
    
    # Invalidate session by pushing last_accessed back
    session_state.last_accessed = datetime.now() - timedelta(seconds=settings.SESSION_TIMEOUT + 10)
    
    # Trigger cleanup
    cleanup_worker = CacheCleanupThread()
    cleanup_worker.cleanup_expired_sessions()
    
    # Now it should be deleted from cache
    assert cache_manager.peek(session_id) is None
    
    # Accessing it via endpoint should return 404
    inspect_res = client.get(f"/api/v1/inspect/{session_id}")
    assert inspect_res.status_code == 404
