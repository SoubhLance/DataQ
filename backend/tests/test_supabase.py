import pytest
import uuid
from app.services.supabase_service import SupabaseService
from app.utils.supabase_client import supabase_client, get_anonymous_user_id

@pytest.fixture(scope="module")
def shared_user_id():
    return get_anonymous_user_id()

def test_supabase_client_init():
    assert supabase_client is not None

def test_supabase_datasets_crud(shared_user_id):
    # Create dataset
    filename = f"test_pytest_{uuid.uuid4().hex[:6]}.csv"
    ds = SupabaseService.create_dataset(
        filename=filename,
        rows=150,
        columns=4,
        file_type="csv",
        user_id=shared_user_id
    )
    assert ds is not None
    assert ds["filename"] == filename
    assert ds["rows"] == 150
    assert ds["columns"] == 4
    assert ds["file_type"] == "csv"
    assert ds["user_id"] == shared_user_id
    
    # Delete dataset
    res_del = supabase_client.table("datasets").delete().eq("id", ds["id"]).execute()
    assert len(res_del.data) == 1

def test_supabase_sessions_crud(shared_user_id):
    # Setup dataset
    filename = f"test_session_ds_{uuid.uuid4().hex[:6]}.csv"
    ds = SupabaseService.create_dataset(
        filename=filename,
        rows=10,
        columns=2,
        file_type="csv",
        user_id=shared_user_id
    )
    
    # Create session
    session_uuid = str(uuid.uuid4())
    sess = SupabaseService.create_session(
        session_id=session_uuid,
        dataset_id=ds["id"],
        status="active"
    )
    assert sess is not None
    assert sess["id"] == session_uuid
    assert sess["dataset_id"] == ds["id"]
    assert sess["status"] == "active"
    
    # Touch session
    SupabaseService.touch_session(session_uuid)
    
    # Clean up (dataset delete cascade cleans session)
    supabase_client.table("datasets").delete().eq("id", ds["id"]).execute()

def test_supabase_operations_crud(shared_user_id):
    # Setup dataset and session
    ds = SupabaseService.create_dataset(
        filename="test_op.csv",
        rows=5,
        columns=1,
        file_type="csv",
        user_id=shared_user_id
    )
    session_uuid = str(uuid.uuid4())
    SupabaseService.create_session(session_uuid, ds["id"])
    
    # Create operation
    op1 = SupabaseService.create_operation(
        session_id=session_uuid,
        step_number=1,
        operation_type="missing",
        parameters={"columns": ["age"], "affected_rows": 2}
    )
    assert op1 is not None
    assert op1["session_id"] == session_uuid
    assert op1["step_number"] == 1
    assert op1["parameters"]["affected_rows"] == 2
    assert op1["parameters"]["is_active"] is True
    
    # Create second operation
    op2 = SupabaseService.create_operation(
        session_id=session_uuid,
        step_number=2,
        operation_type="duplicates",
        parameters={"keep": "first", "affected_rows": 1}
    )
    
    # Fetch active operations
    active_ops = SupabaseService.get_active_operations(session_uuid)
    assert len(active_ops) == 2
    
    # Deactivate last operation (undo)
    deactivated = SupabaseService.deactivate_last_operation(session_uuid)
    assert deactivated is not None
    assert deactivated["step_number"] == 2
    assert deactivated["parameters"]["is_active"] is False
    assert "undone_at" in deactivated["parameters"]
    
    # Re-fetch active operations
    active_ops_after = SupabaseService.get_active_operations(session_uuid)
    assert len(active_ops_after) == 1
    assert active_ops_after[0]["step_number"] == 1
    
    # Clean up (cascade delete)
    supabase_client.table("datasets").delete().eq("id", ds["id"]).execute()

def test_supabase_reports_and_exports(shared_user_id):
    # Setup dataset and session
    ds = SupabaseService.create_dataset(
        filename="test_rep.csv",
        rows=10,
        columns=3,
        file_type="csv",
        user_id=shared_user_id
    )
    session_uuid = str(uuid.uuid4())
    SupabaseService.create_session(session_uuid, ds["id"])
    
    # Create report
    report_db_path = f"reports/{shared_user_id}/{session_uuid}_quality_report.json"
    rep = SupabaseService.create_report(session_uuid, report_db_path)
    assert rep is not None
    assert rep["session_id"] == session_uuid
    assert rep["report_url"] == report_db_path
    
    # Create export
    export_db_path = f"exports/{shared_user_id}/{session_uuid}_cleaned.csv"
    exp = SupabaseService.create_export(session_uuid, "csv", export_db_path)
    assert exp is not None
    assert exp["session_id"] == session_uuid
    assert exp["format"] == "csv"
    assert exp["file_url"] == export_db_path
    
    # Clean up (cascade delete)
    supabase_client.table("datasets").delete().eq("id", ds["id"]).execute()

def test_supabase_storage_operations(shared_user_id):
    test_content = b"Pytest Storage content"
    filename = f"pytest_storage_test_{uuid.uuid4().hex[:6]}.txt"
    storage_path = f"{shared_user_id}/{filename}"
    
    # Upload
    path = SupabaseService.upload_file("uploads", storage_path, test_content)
    assert path == storage_path
    
    # Download
    downloaded = SupabaseService.download_file("uploads", storage_path)
    assert downloaded == test_content
    
    # Generate signed URL
    url = SupabaseService.generate_signed_url("uploads", storage_path, expires_in=120)
    assert url.startswith("http")
    
    # Clean up file
    supabase_client.storage.from_("uploads").remove([storage_path])
