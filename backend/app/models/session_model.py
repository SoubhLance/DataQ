import logging
import pandas as pd
from datetime import datetime
from typing import List
from app.models.operation_model import Operation

logger = logging.getLogger(__name__)

class SessionState:
    """
    In-memory state management representing a dataset cleaning session.
    """
    def __init__(self, session_id: str, filename: str, df: pd.DataFrame):
        self.session_id: str = session_id
        self.filename: str = filename
        self.created_at: datetime = datetime.now()
        self.last_accessed: datetime = datetime.now()
        
        # Supabase database mapping properties
        from app.utils.supabase_client import get_anonymous_user_id
        self.user_id: str = get_anonymous_user_id()
        self.dataset_id: str = None
        
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

    def add_operation(self, op: Operation, affected_rows: int = 0) -> None:
        """Add operation to history and persist to Supabase."""
        self.operations.append(op)
        self.touch()
        
        # Persist to Supabase
        from app.services.supabase_service import SupabaseService
        params = dict(op.params or {})
        params["affected_rows"] = affected_rows
        params["is_active"] = True
        
        try:
            SupabaseService.create_operation(
                session_id=self.session_id,
                step_number=len(self.operations),
                operation_type=op.type,
                parameters=params
            )
        except Exception as e:
            logger.warning(f"Failed to persist operation to Supabase for session {self.session_id}: {e}")
