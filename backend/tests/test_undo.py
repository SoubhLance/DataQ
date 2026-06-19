import os
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from app.utils.dataframe_cache import get_session

@pytest.mark.unit
def test_undo_operations_sequence(client, create_temp_file):
    """
    Apply operations in sequence: duplicates, missing, outliers, encoding, scaling.
    Then undo them all one by one.
    Verify the final dataframe is identical to the original dataframe.
    """
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Save original dataframe for final comparison
    session = get_session(session_id)
    original_df = session.original_df.copy()
    
    # 1. Duplicates removal
    res_dup = client.post(
        "/api/v1/duplicates/remove",
        json={"session_id": session_id, "keep": "first"}
    )
    assert res_dup.status_code == 200
    
    # 2. Missing value imputation
    res_miss = client.post(
        "/api/v1/missing/apply",
        json={"session_id": session_id, "column": "age", "strategy": "median"}
    )
    assert res_miss.status_code == 200
    
    # 3. Outlier removal
    res_out = client.post(
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
    assert res_out.status_code == 200
    
    # 4. Encoding
    res_enc = client.post(
        "/api/v1/columns/encode",
        json={"session_id": session_id, "column": "gender", "method": "label"}
    )
    assert res_enc.status_code == 200
    
    # 5. Scaling
    res_scale = client.post(
        "/api/v1/scaling/apply",
        json={"session_id": session_id, "columns": ["salary"], "method": "standard"}
    )
    assert res_scale.status_code == 200
    
    # Verify current df is modified
    session_current = get_session(session_id)
    assert len(session_current.operations) == 5
    
    # Perform 5 undos
    for i in range(5):
        undo_res = client.post(f"/api/v1/undo/{session_id}")
        assert undo_res.status_code == 200
        
    # Verify operations count is 0
    session_final = get_session(session_id)
    assert len(session_final.operations) == 0
    
    # Confirm final df matches original df
    assert_frame_equal(original_df, session_final.current_df)
