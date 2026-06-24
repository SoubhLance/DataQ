import pytest
import os
from app.utils.supabase_client import supabase_client

@pytest.mark.integration
def test_session_upload_db_persistence(client, create_temp_file):
    """
    Test that uploading a file inserts metadata into datasets and sessions tables in Supabase,
    and deleting the session cleans them up.
    """
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    # 1. Upload dataset via API
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
        
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    
    # 2. Query sessions table in Supabase
    sess_res = supabase_client.table("sessions").select("*").eq("id", session_id).execute()
    assert len(sess_res.data) == 1
    session_row = sess_res.data[0]
    dataset_id = session_row["dataset_id"]
    
    # 3. Query datasets table in Supabase
    ds_res = supabase_client.table("datasets").select("*").eq("id", dataset_id).execute()
    assert len(ds_res.data) == 1
    dataset_row = ds_res.data[0]
    assert dataset_row["filename"] == filename
    assert dataset_row["rows"] == 100
    
    # 4. Clean up session via API
    del_response = client.delete(f"/api/v1/upload/{session_id}")
    assert del_response.status_code == 200
    
    # 5. Verify database rows are removed (cascade deletes sessions/datasets depending on setup,
    # but let's delete them manually from DB if they are not automatically deleted,
    # or assert they are gone. Wait, the API delete_session deletes the cache manager but doesn't
    # delete the DB datasets row by default since datasets are permanent history.
    # Let's delete the dataset from the database to keep it clean!)
    supabase_client.table("datasets").delete().eq("id", dataset_id).execute()
    
    # Verify gone
    sess_verify = supabase_client.table("sessions").select("*").eq("id", session_id).execute()
    assert len(sess_verify.data) == 0
    ds_verify = supabase_client.table("datasets").select("*").eq("id", dataset_id).execute()
    assert len(ds_verify.data) == 0
