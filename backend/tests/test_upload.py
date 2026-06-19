import os
import pytest
from io import BytesIO

@pytest.mark.integration
def test_upload_success_csv(client, create_temp_file):
    """Test successful CSV file upload."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["filename"] == filename
    assert data["rows"] == 100
    assert data["columns"] == 6

@pytest.mark.integration
def test_upload_success_xlsx(client, create_temp_file):
    """Test successful Excel upload."""
    filepath = create_temp_file(".xlsx")
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["filename"] == filename
    assert data["rows"] == 100
    assert data["columns"] == 6

@pytest.mark.integration
def test_upload_success_json(client, create_temp_file):
    """Test successful JSON upload."""
    filepath = create_temp_file(".json")
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "application/json")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["filename"] == filename
    assert data["rows"] == 100
    assert data["columns"] == 6

@pytest.mark.integration
def test_upload_success_parquet(client, create_temp_file):
    """Test successful Parquet upload."""
    filepath = create_temp_file(".parquet")
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "application/octet-stream")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["filename"] == filename
    assert data["rows"] == 100
    assert data["columns"] == 6

@pytest.mark.integration
def test_upload_empty_file(client):
    """Test upload of an empty file (rejection)."""
    response = client.post(
        "/api/v1/upload",
        files={"file": ("empty.csv", BytesIO(b""), "text/csv")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "EMPTY_DATASET" in data["error_code"] or "VALIDATION" in data["error_code"] or "OPERATION_FAILED" in data["error_code"]

@pytest.mark.integration
def test_upload_invalid_extension(client):
    """Test upload with an unsupported extension (e.g. .txt)."""
    response = client.post(
        "/api/v1/upload",
        files={"file": ("invalid.txt", BytesIO(b"some,data,here"), "text/plain")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "UNSUPPORTED_FILE_TYPE"

@pytest.mark.integration
def test_upload_background_success(client, create_temp_file):
    """Test background CSV file upload and task progress status tracking."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        response = client.post(
            "/api/v1/upload?background=True",
            files={"file": (filename, f, "text/csv")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "session_id" in data
    task_id = data["task_id"]
    
    # Check task status endpoint (it should be completed immediately in TestClient)
    task_res = client.get(f"/api/v1/tasks/{task_id}")
    assert task_res.status_code == 200
    task_data = task_res.json()
    assert task_data["status"] == "completed"
    assert task_data["type"] == "upload"
    assert task_data["progress"] == 100
    assert task_data["result"]["filename"] == filename

