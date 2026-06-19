import os
import pytest

@pytest.mark.integration
def test_inspect_dataset(client, create_temp_file):
    """Verify metadata inspect endpoint works correctly."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    # Upload first
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    assert upload_res.status_code == 200
    session_id = upload_res.json()["session_id"]
    
    # Inspect
    inspect_res = client.get(f"/api/v1/inspect/{session_id}")
    assert inspect_res.status_code == 200
    inspect_data = inspect_res.json()
    
    # Check shape
    assert inspect_data["shape"] == [100, 6]
    
    # Check dtypes and columns exist
    cols = inspect_data["columns"]
    col_names = [col["name"] for col in cols]
    assert "id" in col_names
    assert "name" in col_names
    assert "age" in col_names
    assert "salary" in col_names
    assert "gender" in col_names
    assert "date" in col_names
    
    # Check missing count/percent for age
    age_col = next(col for col in cols if col["name"] == "age")
    assert age_col["missing"] == 3
    assert age_col["missing_percent"] == 3.0
    
    # Check numeric vs categorical
    numeric_cols = inspect_data["numeric_columns"]
    categorical_cols = inspect_data["categorical_columns"]
    
    assert "id" in numeric_cols or "id" in categorical_cols  # Depending on profiler classification
    assert "age" in numeric_cols
    assert "salary" in numeric_cols
    assert "name" in categorical_cols
    
    # 2. Quality check
    qual_res = client.get(f"/api/v1/quality/{session_id}")
    assert qual_res.status_code == 200
    qual_data = qual_res.json()
    assert "score" in qual_data
    assert "warnings" in qual_data
    assert isinstance(qual_data["warnings"], list)
    
    # 3. Class imbalance check (on gender target column)
    imb_res = client.get(f"/api/v1/imbalance/{session_id}?target=gender")
    assert imb_res.status_code == 200
    imb_data = imb_res.json()
    assert "ratio" in imb_data
    assert "imbalanced" in imb_data
    assert "class_counts" in imb_data
    
    # 4. Sample endpoint check
    sample_res = client.get(f"/api/v1/sample/{session_id}?limit=15")
    assert sample_res.status_code == 200
    sample_data = sample_res.json()
    assert len(sample_data) == 15
    assert "id" in sample_data[0]
    assert "name" in sample_data[0]

