import os
import pytest
import pandas as pd
import numpy as np

@pytest.mark.unit
def test_label_encoding_preserves_nan(client, create_temp_file):
    """Verify Label Encoding preserves NaN and does not create a 'nan' category."""
    # Create custom dataframe with genders: ["Male", "Female", None, "Male"]
    df = pd.DataFrame({
        "gender": ["Male", "Female", None, "Male"],
        "val": [1, 2, 3, 4]
    })
    
    filepath = create_temp_file(".csv", df)
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Apply Label Encoding
    res = client.post(
        "/api/v1/columns/encode",
        json={"session_id": session_id, "column": "gender", "method": "label"}
    )
    assert res.status_code == 200
    
    # Retrieve the session DataFrame
    from app.utils.dataframe_cache import get_session
    session = get_session(session_id)
    encoded_col = session.current_df["gender"]
    
    # Verify values
    # Encoded values should be [1.0, 0.0, NaN, 1.0] (or [1, 0, None, 1] depending on type)
    # The key point: index 2 should remain NaN/null
    assert pd.isna(encoded_col.iloc[2])
    
    # There should only be two unique non-null codes: 0 and 1
    assert set(encoded_col.dropna()) == {0.0, 1.0}

@pytest.mark.unit
def test_one_hot_encoding(client, create_temp_file):
    """Verify One-Hot Encoding structure, category names, and undo."""
    # Create custom dataframe
    df = pd.DataFrame({
        "gender": ["Male", "Female", None, "Male"],
        "val": [1, 2, 3, 4]
    })
    
    filepath = create_temp_file(".csv", df)
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # 1. Preview
    preview_res = client.post(
        "/api/v1/columns/encode/preview",
        json={"session_id": session_id, "column": "gender", "method": "onehot"}
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["affected_rows"] == 4
    
    # 2. Apply One-Hot Encoding
    res = client.post(
        "/api/v1/columns/encode",
        json={"session_id": session_id, "column": "gender", "method": "onehot"}
    )
    assert res.status_code == 200
    
    from app.utils.dataframe_cache import get_session
    session = get_session(session_id)
    cols = list(session.current_df.columns)
    
    # original column 'gender' should be dropped
    assert "gender" not in cols
    # new columns 'gender_Female' and 'gender_Male' should exist (and potentially gender_None or gender_nan depending on pandas behavior)
    assert "gender_Female" in cols
    assert "gender_Male" in cols
    
    # 3. Undo
    undo_res = client.post(f"/api/v1/undo/{session_id}")
    assert undo_res.status_code == 200
    
    session_after_undo = get_session(session_id)
    cols_after_undo = list(session_after_undo.current_df.columns)
    assert "gender" in cols_after_undo
    assert "gender_Female" not in cols_after_undo
    assert "gender_Male" not in cols_after_undo
