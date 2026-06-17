import pandas as pd
from datetime import datetime
from typing import List
from app.models.operation_model import Operation

class SessionState:
    """
    In-memory state management representing a dataset cleaning session.
    """
    def __init__(self, session_id: str, filename: str, df: pd.DataFrame):
        self.session_id: str = session_id
        self.filename: str = filename
        self.created_at: datetime = datetime.now()
        self.last_accessed: datetime = datetime.now()
        
        # Save exact copy of the original dataset for replay/undo
        self.original_df: pd.DataFrame = df.copy()
        # The working copy that gets updated
        self.current_df: pd.DataFrame = df
        
        self.rows: int = len(df)
        self.columns: int = len(df.columns)
        self.operations: List[Operation] = []
        
        # Track associated files for safe deletion
        self.uploaded_filepath = None
        self.cleaned_filepaths = []
        self.report_filepaths = []

    def touch(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed = datetime.now()

    def update_dataframe(self, new_df: pd.DataFrame) -> None:
        """Update the working DataFrame and dimensions."""
        self.current_df = new_df
        self.rows = len(new_df)
        self.columns = len(new_df.columns)
        self.touch()
