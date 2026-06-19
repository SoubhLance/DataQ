import os
import pytest

@pytest.mark.unit
def test_visualization_endpoints(client, create_temp_file):
    """Verify that all visualization data generation endpoints return correct schemas."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # 1. Missing heatmap data
    missing_res = client.get(f"/api/v1/visualization/missing/{session_id}")
    assert missing_res.status_code == 200
    missing_data = missing_res.json()
    assert isinstance(missing_data, list)
    if len(missing_data) > 0:
        assert "row_index" in missing_data[0]
        assert "age" in missing_data[0]
        
    # 2. Correlation heatmap data
    corr_res = client.get(f"/api/v1/visualization/correlation/{session_id}")
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert isinstance(corr_data, list)
    if len(corr_data) > 0:
        assert "x" in corr_data[0]
        assert "y" in corr_data[0]
        assert "value" in corr_data[0]
        
    # 3. Distribution histogram data
    dist_res = client.get(f"/api/v1/visualization/distribution/{session_id}?column=salary&bins=12")
    assert dist_res.status_code == 200
    dist_data = dist_res.json()
    assert isinstance(dist_data, list)
    if len(dist_data) > 0:
        assert "bin_start" in dist_data[0]
        assert "bin_end" in dist_data[0]
        assert "count" in dist_data[0]
        
    # 4. Boxplot statistics data
    box_res = client.get(f"/api/v1/visualization/boxplot/{session_id}?column=salary")
    assert box_res.status_code == 200
    box_data = box_res.json()
    assert "min" in box_data
    assert "q1" in box_data
    assert "median" in box_data
    assert "q3" in box_data
    assert "max" in box_data
    assert box_data["column"] == "salary"
