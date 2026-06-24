import pytest
import os
import json
from app.utils.supabase_client import supabase_client

@pytest.mark.integration
def test_report_db_and_storage(client, create_temp_file):
    """
    Test that generating a JSON report uploads it to Supabase Storage and logs it in the reports table.
    """
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    # 1. Upload dataset to get a session
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    
    # 2. Trigger report generation
    report_res = client.post(f"/api/v1/export/json-report?session_id={session_id}")
    assert report_res.status_code == 200
    
    # 3. Retrieve report record from Supabase
    rep_query = supabase_client.table("reports").select("*").eq("session_id", session_id).execute()
    assert len(rep_query.data) >= 1
    report_record = rep_query.data[-1]
    
    storage_path_full = report_record["report_url"] # e.g. "reports/uid/session_quality_report.json"
    assert storage_path_full.startswith("reports/")
    
    # Strip prefix bucket name 'reports/' to get actual storage path
    storage_path = storage_path_full.replace("reports/", "")
    
    # 4. Check that file exists in reports storage
    downloaded_bytes = supabase_client.storage.from_("reports").download(storage_path)
    assert len(downloaded_bytes) > 0
    
    report_json = json.loads(downloaded_bytes.decode("utf-8"))
    assert report_json["summary"]["session_id"] == session_id
    assert "quality_score" in report_json
    
    # 5. Clean up storage and DB
    supabase_client.storage.from_("reports").remove([storage_path])
    
    # Fetch session dataset_id to cascade clean
    sess_res = supabase_client.table("sessions").select("dataset_id").eq("id", session_id).execute()
    if sess_res.data:
        supabase_client.table("datasets").delete().eq("id", sess_res.data[0]["dataset_id"]).execute()
