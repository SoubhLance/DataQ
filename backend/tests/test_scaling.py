import os
import pytest
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
import pandas as pd

@pytest.mark.unit
def test_scaling_standard(client, create_temp_file):
    """Test standard scaling apply and preview."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # 1. Preview (age and salary are numeric)
    preview_res = client.post(
        "/api/v1/scaling/preview",
        json={"session_id": session_id, "columns": ["salary"], "method": "standard"}
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["affected_rows"] == 100
    assert len(preview_data["sample_before"]) == 10
    assert len(preview_data["sample_after"]) == 10
    
    # 2. Apply
    apply_res = client.post(
        "/api/v1/scaling/apply",
        json={"session_id": session_id, "columns": ["salary"], "method": "standard"}
    )
    assert apply_res.status_code == 200
    
    # Inspect and verify columns are scaled
    # Scaled values of salary should have mean close to 0 and std close to 1
    # Retrieve the session to compare
    from app.utils.dataframe_cache import get_session
    session = get_session(session_id)
    scaled_salary = session.current_df["salary"]
    assert np.isclose(scaled_salary.mean(), 0.0, atol=1e-7)
    assert np.isclose(scaled_salary.std(ddof=0), 1.0, atol=1e-7)

@pytest.mark.unit
def test_scaling_minmax(client, create_temp_file):
    """Test minmax scaling apply."""
    filepath = create_temp_file(".csv")
    filename = os.urandom(4).hex() + ".csv"
    
    # Use simple custom dataframe to verify MinMax range [0, 1]
    df = pd.DataFrame({"val": [10.0, 20.0, 30.0, 40.0, 50.0]})
    custom_filepath = os.path.join(os.path.dirname(filepath), filename)
    df.to_csv(custom_filepath, index=False)
    
    with open(custom_filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    apply_res = client.post(
        "/api/v1/scaling/apply",
        json={"session_id": session_id, "columns": ["val"], "method": "minmax"}
    )
    assert apply_res.status_code == 200
    
    from app.utils.dataframe_cache import get_session
    session = get_session(session_id)
    scaled_vals = session.current_df["val"]
    assert scaled_vals.min() == 0.0
    assert scaled_vals.max() == 1.0
    
    os.remove(custom_filepath)

@pytest.mark.unit
def test_scaling_robust(client, create_temp_file):
    """Test robust scaling apply."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    apply_res = client.post(
        "/api/v1/scaling/apply",
        json={"session_id": session_id, "columns": ["salary"], "method": "robust"}
    )
    assert apply_res.status_code == 200
