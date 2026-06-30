import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

@pytest.mark.integration
@patch("app.ml.models.sentence_model.encode")
@patch("app.ml.models.sentence_model.encode_single")
def test_get_recommendations_endpoint(mock_encode_single, mock_encode, client, create_temp_file):
    # Setup mocks for SBERT model to avoid network download
    import numpy as np
    mock_encode.return_value = np.zeros((37, 384)) # 37 algorithms in the KB
    mock_encode_single.return_value = np.zeros(384)

    # 1. Upload a CSV dataset to create an active session
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    assert upload_res.status_code == 200
    session_id = upload_res.json()["session_id"]
    
    # 2. Call recommendations endpoint
    rec_res = client.post(
        "/api/v1/ml/recommend",
        json={
            "session_id": session_id,
            "target_column": "age",
            "problem_type": "regression",
            "goal": "predict user age based on other features"
        }
    )
    
    assert rec_res.status_code == 200
    data = rec_res.json()
    
    assert data["session_id"] == session_id
    assert data["problem_type"] == "regression"
    assert "dataset_profile" in data
    assert "recommendations" in data
    assert "alternatives" in data
    assert "suggested_pipeline" in data
    assert "pipeline_code" in data
    
    primary = data["recommendations"]
    assert primary["id"] is not None
    assert primary["role"] == "recommended"
    assert "explainability" in primary
    
    # Verify we got alternatives table
    assert len(data["alternatives"]) > 0
    alt = data["alternatives"][0]
    assert "algorithm" in alt
    assert "role" in alt
    assert "speed" in alt
    assert "accuracy" in alt
    
    # Verify pipeline code is generated and contains sklearn imports
    assert "Pipeline" in data["pipeline_code"]

def test_get_recommendations_invalid_session(client):
    # 1. Invalid UUID format should raise ValidationException and return 400
    rec_res = client.post(
        "/api/v1/ml/recommend",
        json={
            "session_id": "invalid-session-id-1234",
            "target_column": "target"
        }
    )
    assert rec_res.status_code == 400
    assert "Invalid session ID format" in rec_res.json()["message"]

    # 2. Valid UUID format but non-existent session should return 404
    rec_res_not_found = client.post(
        "/api/v1/ml/recommend",
        json={
            "session_id": "00000000-0000-0000-0000-000000000000",
            "target_column": "target"
        }
    )
    assert rec_res_not_found.status_code == 404
    assert "not found" in rec_res_not_found.json()["message"].lower()
