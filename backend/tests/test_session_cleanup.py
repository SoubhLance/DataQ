import os
import pytest
from app.utils.dataframe_cache import cache_manager

@pytest.mark.integration
def test_session_cleanup_flow(client, create_temp_file):
    """
    Verify that calling DELETE /api/v1/upload/{session_id} removes the session
    from cache and deletes all associated files (uploads, cleaned, reports) from disk.
    """
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    # 1. Upload dataset
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    assert upload_res.status_code == 200
    session_id = upload_res.json()["session_id"]
    
    # Verify in cache and upload file exists
    session = cache_manager.peek(session_id)
    assert session is not None
    uploaded_file = session.uploaded_filepath
    assert os.path.exists(uploaded_file)
    
    # 2. Export file to populate cleaned_filepaths
    export_res = client.post(f"/api/v1/export/file/{session_id}?format=csv")
    assert export_res.status_code == 200
    
    assert len(session.cleaned_filepaths) == 1
    cleaned_file = session.cleaned_filepaths[0]
    assert os.path.exists(cleaned_file)
    
    # 3. Generate report to populate report_filepaths
    report_res = client.post(f"/api/v1/export/json-report?session_id={session_id}")
    assert report_res.status_code == 200
    
    assert len(session.report_filepaths) == 1
    report_file = session.report_filepaths[0]
    assert os.path.exists(report_file)
    
    # 4. Trigger manual deletion
    delete_res = client.delete(f"/api/v1/upload/{session_id}")
    assert delete_res.status_code == 200
    
    # 5. Assertions
    # Cache should be removed
    assert cache_manager.peek(session_id) is None
    
    # Files should be removed from disk
    assert not os.path.exists(uploaded_file)
    assert not os.path.exists(cleaned_file)
    assert not os.path.exists(report_file)
