import os
import pytest
import pandas as pd
import numpy as np

@pytest.mark.unit
def test_missing_imputation_mean(client, create_temp_file):
    """Test mean imputation on numerical column."""
    # Let's upload a dataset and run mean imputation
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # 1. Preview
    preview_res = client.post(
        "/api/v1/missing/preview",
        json={"session_id": session_id, "column": "age", "strategy": "mean"}
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["affected_rows"] == 3
    
    # 2. Apply Mean Imputation
    apply_res = client.post(
        "/api/v1/missing/apply",
        json={"session_id": session_id, "column": "age", "strategy": "mean"}
    )
    assert apply_res.status_code == 200
    
    # Inspect to see that age column no longer has missing values
    inspect_res = client.get(f"/api/v1/inspect/{session_id}")
    cols = inspect_res.json()["columns"]
    age_col = next(col for col in cols if col["name"] == "age")
    assert age_col["missing"] == 0
    
    # But other columns (gender) still have missing values (NaN preservation)
    gender_col = next(col for col in cols if col["name"] == "gender")
    assert gender_col["missing"] > 0

@pytest.mark.unit
def test_missing_imputation_median(client, create_temp_file):
    """Test median imputation on numerical column."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    apply_res = client.post(
        "/api/v1/missing/apply",
        json={"session_id": session_id, "column": "age", "strategy": "median"}
    )
    assert apply_res.status_code == 200
    
    inspect_res = client.get(f"/api/v1/inspect/{session_id}")
    cols = inspect_res.json()["columns"]
    age_col = next(col for col in cols if col["name"] == "age")
    assert age_col["missing"] == 0

@pytest.mark.unit
def test_missing_imputation_mode(client, create_temp_file):
    """Test mode imputation on categorical/string column."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    apply_res = client.post(
        "/api/v1/missing/apply",
        json={"session_id": session_id, "column": "gender", "strategy": "mode"}
    )
    assert apply_res.status_code == 200
    
    inspect_res = client.get(f"/api/v1/inspect/{session_id}")
    cols = inspect_res.json()["columns"]
    gender_col = next(col for col in cols if col["name"] == "gender")
    assert gender_col["missing"] == 0

@pytest.mark.unit
def test_missing_imputation_constant(client, create_temp_file):
    """Test constant imputation with appropriate type casting."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Apply constant value on numeric column (e.g. age = "99")
    apply_res = client.post(
        "/api/v1/missing/apply",
        json={"session_id": session_id, "column": "age", "strategy": "constant", "constant_value": "99"}
    )
    assert apply_res.status_code == 200
    
    # Inspect to ensure age is cast properly
    inspect_res = client.get(f"/api/v1/inspect/{session_id}")
    cols = inspect_res.json()["columns"]
    age_col = next(col for col in cols if col["name"] == "age")
    assert age_col["missing"] == 0
