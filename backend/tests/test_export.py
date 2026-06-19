import os
import pytest

@pytest.mark.integration
def test_export_endpoints(client, create_temp_file):
    """Verify CSV export and JSON report export work and return valid responses."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # 1. Export Cleaned CSV via POST /export/file/{session_id}?format=csv
    export_res = client.post(f"/api/v1/export/file/{session_id}?format=csv")
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    assert "cleaned_" in export_res.headers["content-disposition"]
    
    # 2. Export Cleaned CSV via deprecated/standard POST /export/csv
    export_csv_res = client.post(f"/api/v1/export/csv?session_id={session_id}")
    assert export_csv_res.status_code == 200
    assert "text/csv" in export_csv_res.headers["content-type"]
    
    # 3. Export JSON report via POST /export/json-report
    report_res = client.post(f"/api/v1/export/json-report?session_id={session_id}")
    assert report_res.status_code == 200
    report_data = report_res.json()
    
    # Verify report schema
    assert "summary" in report_data
    assert "quality_score" in report_data
    assert "duplicates" in report_data
    assert "missing" in report_data
    assert "outliers" in report_data
    
    # Check details inside
    assert report_data["summary"]["total_rows"] == 100
    assert report_data["summary"]["total_columns"] == 6
    assert "score" in report_data["quality_score"]

