import os
import pytest
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from app.utils.dataframe_cache import get_session

@pytest.mark.slow
def test_concurrency_and_session_isolation(client, create_temp_file):
    """
    Test concurrency:
    1. Upload datasets for 10 sessions concurrently using a ThreadPoolExecutor.
    2. Run operations on different sessions concurrently.
    3. Verify that each session remains isolated with no cache contamination.
    """
    num_sessions = 10
    
    # Helper function to run in threads
    def create_session_and_modify(index):
        # Create a dataframe specific to this thread
        df = pd.DataFrame({
            "col_thread": [index] * 10,
            "val": list(range(10))
        })
        
        # Save dataframe to a file
        filename = f"concurrency_{index}.csv"
        filepath = os.path.join(os.path.dirname(create_temp_file(".csv")), filename)
        df.to_csv(filepath, index=False)
        
        # Upload
        with open(filepath, "rb") as f:
            upload_res = client.post(
                "/api/v1/upload",
                files={"file": (filename, f, "text/csv")}
            )
        assert upload_res.status_code == 200
        session_id = upload_res.json()["session_id"]
        
        # Modify this session: rename 'val' to f'val_{index}'
        rename_res = client.post(
            "/api/v1/columns/rename",
            json={"session_id": session_id, "old_name": "val", "new_name": f"val_{index}"}
        )
        assert rename_res.status_code == 200
        
        # Cleanup temp file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
                
        return session_id, index

    # Execute uploads and modifications concurrently across 10 threads
    with ThreadPoolExecutor(max_workers=num_sessions) as executor:
        results = list(executor.map(create_session_and_modify, range(num_sessions)))
        
    # Verify isolation
    for session_id, index in results:
        session = get_session(session_id)
        
        # The dataframe must contain 'col_thread' filled with the thread's index
        assert session.current_df["col_thread"].iloc[0] == index
        
        # The column 'val' must have been renamed to f'val_{index}'
        assert f"val_{index}" in session.current_df.columns
        assert "val" not in session.current_df.columns
        
        # Ensure session.filename is correct
        assert session.filename == f"concurrency_{index}.csv"
