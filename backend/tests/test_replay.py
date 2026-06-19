import os
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from app.utils.dataframe_cache import get_session
from app.services.pipeline_service import PipelineService

@pytest.mark.slow
def test_replay_fifty_operations(client, create_temp_file):
    """
    Apply 50 column renaming operations sequentially.
    Verify that replaying all operations yields a DataFrame identical to the final current DataFrame.
    """
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # We will rename the column 'name' 50 times:
    # name -> name_1 -> name_2 -> ... -> name_50
    old_name = "name"
    for i in range(1, 51):
        new_name = f"name_{i}"
        res = client.post(
            "/api/v1/columns/rename",
            json={"session_id": session_id, "old_name": old_name, "new_name": new_name}
        )
        assert res.status_code == 200
        old_name = new_name
        
    session = get_session(session_id)
    assert len(session.operations) == 50
    
    # Save the current state of dataframe before manual replay
    df_current_before_replay = session.current_df.copy()
    
    # Run replay
    PipelineService.replay_all_operations(session)
    
    # Assert that the current dataframe after replay is identical to what it was before replay
    assert_frame_equal(session.current_df, df_current_before_replay)
