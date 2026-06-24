import pytest
import os
from app.utils.supabase_client import supabase_client

@pytest.mark.integration
def test_export_file_db_and_storage(client, create_temp_file):
    """
    Test that exporting a file uploads it to Supabase Storage and logs it in the exports table.
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
    
    # 2. Trigger CSV Export
    export_res = client.post(f"/api/v1/export/file/{session_id}?format=csv")
    assert export_res.status_code == 200
    
    # 3. Retrieve export record from Supabase
    exp_query = supabase_client.table("exports").select("*").eq("session_id", session_id).execute()
    assert len(exp_query.data) >= 1
    export_record = exp_query.data[-1]
    assert export_record["format"] == "csv"
    
    # Storage path is stored in file_url
    storage_path_full = export_record["file_url"] # e.g. "exports/uid/session_cleaned.csv"
    assert storage_path_full.startswith("exports/")
    
    # Strip prefix bucket name 'exports/' to get actual storage path
    storage_path = storage_path_full.replace("exports/", "")
    
    # 4. Check that file exists in exports storage
    downloaded_bytes = supabase_client.storage.from_("exports").download(storage_path)
    assert len(downloaded_bytes) > 0
    
    # 5. Clean up storage and DB
    supabase_client.storage.from_("exports").remove([storage_path])
    
    # Fetch session dataset_id to cascade clean
    sess_res = supabase_client.table("sessions").select("dataset_id").eq("id", session_id).execute()
    if sess_res.data:
        supabase_client.table("datasets").delete().eq("id", sess_res.data[0]["dataset_id"]).execute()

@pytest.mark.integration
def test_export_pipeline_db_and_storage(client, create_temp_file):
    """
    Test that fetching the pipeline code uploads it to Supabase Storage and logs it in the exports table.
    """
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = response.json()["session_id"]
    
    # Fetch pipeline pandas code
    pipeline_res = client.get(f"/api/v1/pipeline/{session_id}?format=pandas")
    assert pipeline_res.status_code == 200
    
    # Retrieve export record
    exp_query = supabase_client.table("exports").select("*").eq("session_id", session_id).execute()
    assert len(exp_query.data) >= 1
    export_record = exp_query.data[-1]
    assert export_record["format"] == "python"
    
    storage_path_full = export_record["file_url"]
    storage_path = storage_path_full.replace("exports/", "")
    
    # Verify file in storage
    downloaded = supabase_client.storage.from_("exports").download(storage_path)
    assert b"import pandas" in downloaded or b"df =" in downloaded
    
    # Cleanup
    supabase_client.storage.from_("exports").remove([storage_path])
    sess_res = supabase_client.table("sessions").select("dataset_id").eq("id", session_id).execute()
    if sess_res.data:
        supabase_client.table("datasets").delete().eq("id", sess_res.data[0]["dataset_id"]).execute()
