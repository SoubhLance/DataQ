import os
import pytest

@pytest.mark.unit
def test_duplicate_operations(client, create_temp_file):
    """Verify duplicates detection, preview, apply removal, and undo."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    # Upload
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    assert upload_res.status_code == 200
    session_id = upload_res.json()["session_id"]
    
    # 1. Detect duplicates
    detect_res = client.get(f"/api/v1/duplicates/{session_id}")
    assert detect_res.status_code == 200
    detect_data = detect_res.json()
    assert detect_data["duplicate_rows"] == 2 # Row 30 and 40 were made duplicates of 20
    
    # 2. Preview duplicate removal
    preview_res = client.post(
        "/api/v1/duplicates/preview",
        json={"session_id": session_id, "keep": "first"}
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["affected_rows"] == 2
    
    # 3. Apply removal
    remove_res = client.post(
        "/api/v1/duplicates/remove",
        json={"session_id": session_id, "keep": "first"}
    )
    assert remove_res.status_code == 200
    remove_data = remove_res.json()
    assert remove_data["status"] == "success"
    assert remove_data["rows_remaining"] == 98 # 100 - 2 = 98
    
    # Verify duplicate count is now zero
    detect_res2 = client.get(f"/api/v1/duplicates/{session_id}")
    assert detect_res2.status_code == 200
    assert detect_res2.json()["duplicate_rows"] == 0
    
    # 4. Undo duplicate removal
    undo_res = client.post(f"/api/v1/undo/{session_id}")
    assert undo_res.status_code == 200
    undo_data = undo_res.json()
    assert undo_data["status"] == "success"
    assert undo_data["rows"] == 100
    
    # Verify duplicate count is back to 2
    detect_res3 = client.get(f"/api/v1/duplicates/{session_id}")
    assert detect_res3.json()["duplicate_rows"] == 2
