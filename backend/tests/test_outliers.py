import os
import pytest

@pytest.mark.unit
def test_outliers_iqr(client, create_temp_file):
    """Test IQR outlier detection and removal."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # 1. Detect Outliers (IQR)
    detect_res = client.get(f"/api/v1/outliers/{session_id}?method=iqr")
    assert detect_res.status_code == 200
    detect_data = detect_res.json()
    # Check that salary column lists some outliers (we added 3 outliers manually)
    salary_col = next(col for col in detect_data["columns"] if col["column"] == "salary")
    assert salary_col["outliers"] >= 2
    
    # 2. Preview
    preview_res = client.post(
        "/api/v1/outliers/preview",
        json={
            "session_id": session_id,
            "column": "salary",
            "method": "iqr",
            "action": "remove",
            "threshold": 3.0,
            "contamination": 0.05
        }
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["affected_rows"] >= 2
    
    # 3. Apply treatment (remove)
    remove_res = client.post(
        "/api/v1/outliers/remove",
        json={
            "session_id": session_id,
            "column": "salary",
            "method": "iqr",
            "action": "remove",
            "threshold": 3.0,
            "contamination": 0.05
        }
    )
    assert remove_res.status_code == 200
    
    # Check that outliers were removed (max and min values should be within IQR limits)
    from app.utils.dataframe_cache import get_session
    session = get_session(session_id)
    assert session.current_df["salary"].max() < 150000.0
    assert session.current_df["salary"].min() > 0.0

@pytest.mark.unit
def test_outliers_zscore(client, create_temp_file):
    """Test Z-score outlier detection and capping."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Apply capping using zscore
    cap_res = client.post(
        "/api/v1/outliers/remove",
        json={
            "session_id": session_id,
            "column": "salary",
            "method": "zscore",
            "action": "cap",
            "threshold": 2.0,
            "contamination": 0.05
        }
    )
    assert cap_res.status_code == 200
    
    # Verify that Z-score outliers are capped
    from app.utils.dataframe_cache import get_session
    session = get_session(session_id)
    assert session.current_df["salary"].max() < 150000.0
    assert session.current_df["salary"].min() > 0.0

@pytest.mark.unit
def test_outliers_isolation_forest(client, create_temp_file):
    """Test Isolation Forest outlier detection."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    detect_res = client.get(f"/api/v1/outliers/{session_id}?method=iforest&contamination=0.05")
    assert detect_res.status_code == 200
    detect_data = detect_res.json()
    salary_col = next(col for col in detect_data["columns"] if col["column"] == "salary")
    assert salary_col["outliers"] > 0
