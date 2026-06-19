import os
import pytest
import pandas as pd
import numpy as np

@pytest.mark.unit
def test_correlation_small_dataset(client, create_temp_file):
    """Test correlation endpoint with a small dataset (20 columns)."""
    # Generate 20 numerical columns
    cols = {f"col_{i}": np.random.randn(50) for i in range(20)}
    df = pd.DataFrame(cols)
    
    filepath = create_temp_file(".csv", df)
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    response = client.get(f"/api/v1/correlation/{session_id}?threshold=0.5")
    assert response.status_code == 200
    data = response.json()
    assert "matrix" in data
    assert "highly_correlated" in data
    assert data.get("warning") is None

@pytest.mark.slow
def test_correlation_large_dataset(client, create_temp_file):
    """Test correlation endpoint with a large dataset (350 columns) to ensure it returns a warning and doesn't crash."""
    # Generate 350 columns
    cols = {f"col_{i}": np.random.randn(10) for i in range(350)}
    df = pd.DataFrame(cols)
    
    filepath = create_temp_file(".csv", df)
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    response = client.get(f"/api/v1/correlation/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert "warning" in data
    assert "Correlation computation skipped" in data["warning"]
    assert data["matrix"] == {}
    assert data["highly_correlated"] == []
