import pytest
from io import BytesIO

@pytest.mark.integration
def test_magic_bytes_fake_csv_zip(client):
    """Test uploading a ZIP file masquerading as a CSV file."""
    # ZIP signature is PK\x03\x04
    fake_csv_content = b"PK\x03\x04\x14\x00\x08\x00\x08\x00"
    response = client.post(
        "/api/v1/upload",
        files={"file": ("fake.csv", BytesIO(fake_csv_content), "text/csv")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "VALIDATION_FAILED" in data["error_code"] or "FILE" in data["error_code"]
    assert "zip/parquet signature" in data["message"] or "binary null bytes" in data["message"]

@pytest.mark.integration
def test_magic_bytes_renamed_exe(client):
    """Test uploading an EXE file masquerading as a CSV file."""
    # EXE files start with MZ and contain null bytes
    fake_exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff"
    response = client.post(
        "/api/v1/upload",
        files={"file": ("fake_exe.csv", BytesIO(fake_exe_content), "text/csv")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "VALIDATION_FAILED" in data["error_code"]
    assert "null bytes" in data["message"]

@pytest.mark.integration
def test_magic_bytes_corrupted_parquet(client):
    """Test uploading a corrupted Parquet file."""
    # Parquet should start with PAR1 but here we pass invalid bytes
    corrupt_parquet = b"NOTPAR1_some_corrupt_bytes"
    response = client.post(
        "/api/v1/upload",
        files={"file": ("corrupt.parquet", BytesIO(corrupt_parquet), "application/octet-stream")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "VALIDATION_FAILED" in data["error_code"]
    assert "Parquet format" in data["message"]
