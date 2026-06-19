import os
import pytest
import pandas as pd
import numpy as np
from app.exceptions.dataset_exceptions import ColumnNotFound, InvalidDtype, EmptyDataset, OperationError
from app.services.task_service import task_service
from app.services.recommendation_service import RecommendationService
from app.utils.validators import validate_column_dtype_compatibility, safe_resolve_path, sanitize_session_id
from app.exceptions.validation_exceptions import ValidationException
from app.utils.dataframe_cache import get_session

@pytest.mark.unit
def test_dataset_exceptions_coverage():
    """Trigger exceptions directly to cover their constructors and properties."""
    with pytest.raises(ColumnNotFound) as exc:
        raise ColumnNotFound("col_abc")
    assert "col_abc" in str(exc.value)
    
    with pytest.raises(InvalidDtype) as exc:
        raise InvalidDtype("col_abc", "int", "decimal part exists")
    assert "Cannot cast" in str(exc.value)
    
    with pytest.raises(EmptyDataset) as exc:
        raise EmptyDataset()
    assert "empty" in str(exc.value)
    
    with pytest.raises(OperationError) as exc:
        raise OperationError("Casting", "failed")
    assert "Casting" in str(exc.value)

@pytest.mark.unit
def test_task_service_edge_cases():
    """Trigger missing paths and fail paths in task_service to achieve 100% coverage."""
    # Try updating non-existent task
    task_service.update_task_progress("non_existent_id", 50, "no msg")
    
    # Try completing non-existent task
    task_service.complete_task("non_existent_id")
    
    # Try failing non-existent task
    task_service.fail_task("non_existent_id", "some error")
    
    # Create valid task and then fail it
    task = task_service.create_task("session_xyz", "scaling")
    assert task.status.value == "queued"
    
    task_service.fail_task(task.task_id, "scale error")
    failed_task = task_service.get_task(task.task_id)
    assert failed_task.status.value == "failed"
    assert failed_task.error == "scale error"

@pytest.mark.unit
def test_recommendation_service_coverage(client, create_temp_file):
    """Call encoding and outlier recommendation logic to cover recommendation_service.py."""
    # Create sample dataframe with categorical and outliers
    df = pd.DataFrame({
        "cat_low": ["A", "B", "A", "B", "A"] * 10, # 2 unique
        "cat_high": [f"Val_{i}" for i in range(10)] + [f"Val_{i}" for i in range(10)] * 4, # 10 unique
        "num_outliers": [1.0] * 47 + [100.0, -100.0, 50.0], # 50 rows, outliers exist
    })
    
    filepath = create_temp_file(".csv", df)
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    session = get_session(session_id)
    
    # Run recommendation service directly
    enc_recs = RecommendationService.get_encoding_recommendations(session)
    assert len(enc_recs) == 2
    
    outlier_recs = RecommendationService.get_outlier_recommendations(session)
    assert len(outlier_recs) > 0

@pytest.mark.unit
def test_validator_compatibility_checks():
    """Verify validator casting compatibilities cover all conditional branches."""
    # Int casting checks
    df_valid = pd.DataFrame({"col": [1.0, 2.0, 3.0]})
    validate_column_dtype_compatibility(df_valid, "col", "int") # valid
    
    df_invalid_int = pd.DataFrame({"col": ["abc", "2.0"]})
    with pytest.raises(InvalidDtype):
        validate_column_dtype_compatibility(df_invalid_int, "col", "int")
        
    # Float casting checks
    df_invalid_float = pd.DataFrame({"col": ["not-a-number", "2.0"]})
    with pytest.raises(InvalidDtype):
        validate_column_dtype_compatibility(df_invalid_float, "col", "float")
        
    # Datetime casting checks
    df_invalid_date = pd.DataFrame({"col": ["not-a-date", "2026-06-19"]})
    with pytest.raises(InvalidDtype):
        validate_column_dtype_compatibility(df_invalid_date, "col", "datetime")
        
    # Unsupported target checks
    with pytest.raises(InvalidDtype) as exc:
        validate_column_dtype_compatibility(df_valid, "col", "unsupported_type")
    assert "Unsupported target" in str(exc.value)

@pytest.mark.integration
def test_websocket_manager_and_endpoint(client, create_temp_file):
    """Test websocket connections and message exchange."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Establish WebSocket connection
    with client.websocket_connect(f"/api/v1/ws/session/{session_id}") as ws:
        ws.send_text("ping")
        # Websocket runs in background and logs/keeps alive
        
    # Test invalid session close violation
    with pytest.raises(Exception): # starlette websocket close raising policies
        with client.websocket_connect("/api/v1/ws/session/invalid-uuid-format") as ws:
            pass
