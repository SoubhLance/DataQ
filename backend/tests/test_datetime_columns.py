import os
import pytest
import pandas as pd
from app.core.profiler import DatasetProfiler
from app.services.pipeline_service import PipelineService

@pytest.mark.unit
def test_datetime_detection_and_preservation(client, create_temp_file):
    """Test datetime column detection, casting, preservation, and replay."""
    # Create custom dataframe with explicit date string column and already datetime column
    df = pd.DataFrame({
        "date_str": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        "num_val": [1, 2, 3, 4]
    })
    
    # 1. Test DatasetProfiler detection directly
    profiler = DatasetProfiler(df)
    assert "date_str" in profiler.datetime_columns
    
    # 2. Upload and test casting via API
    filepath = create_temp_file(".csv", df)
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Cast "date_str" column to datetime
    cast_res = client.post(
        "/api/v1/columns/change_dtype",
        json={"session_id": session_id, "column": "date_str", "new_dtype": "datetime"}
    )
    assert cast_res.status_code == 200
    
    # Verify in session that the datatype is indeed datetime (or datetime64[ns])
    from app.utils.dataframe_cache import get_session
    session = get_session(session_id)
    assert pd.api.types.is_datetime64_any_dtype(session.current_df["date_str"])
    
    # 3. Verify Replay correctness
    # If we replay the operations in the session history, the column is correctly cast
    PipelineService.replay_all_operations(session)
    assert pd.api.types.is_datetime64_any_dtype(session.current_df["date_str"])
