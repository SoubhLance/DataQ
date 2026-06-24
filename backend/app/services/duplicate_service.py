import pandas as pd
from typing import Tuple, Dict, Any, List
from app.models.session_model import SessionState
from app.models.operation_model import Operation
from app.schemas.duplicate_schema import DuplicateDetectResponse, DuplicatePreviewResponse, KeepOption

class DuplicateService:
    """
    Service responsible for duplicate rows detection and removal.
    """
    @staticmethod
    def detect_duplicates(session: SessionState) -> DuplicateDetectResponse:
        """
        Identify total duplicates in the dataset.
        """
        df = session.current_df
        total_rows = len(df)
        duplicate_rows = int(df.duplicated().sum())
        duplicate_percent = float((duplicate_rows / total_rows) * 100) if total_rows > 0 else 0.0
        
        return DuplicateDetectResponse(
            total_rows=total_rows,
            duplicate_rows=duplicate_rows,
            duplicate_percent=round(duplicate_percent, 2)
        )

    @staticmethod
    def preview_remove(session: SessionState, keep: KeepOption) -> DuplicatePreviewResponse:
        """
        Preview the outcome of removing duplicates.
        """
        df = session.current_df
        keep_val = DuplicateService._get_keep_value(keep)
        
        # Identify duplicate rows (rows that will be removed)
        duplicate_mask = df.duplicated(keep=keep_val)
        duplicate_rows = df[duplicate_mask]
        affected_count = len(duplicate_rows)
        
        # Take sample of duplicates (up to 10)
        sample_before = duplicate_rows.head(10).replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        
        # Preview after removal
        df_cleaned = df.drop_duplicates(keep=keep_val)
        sample_after = df_cleaned.head(10).replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        
        return DuplicatePreviewResponse(
            affected_rows=affected_count,
            sample_before=sample_before,
            sample_after=sample_after
        )

    @staticmethod
    def apply_remove(session: SessionState, keep: KeepOption) -> None:
        """
        Remove duplicate rows from dataset, update session state, and record operation.
        """
        df = session.current_df
        keep_val = DuplicateService._get_keep_value(keep)
        
        # Remove duplicates
        df_cleaned = df.drop_duplicates(keep=keep_val)
        
        # Create Operation
        keep_param_str = f"'{keep_val}'" if isinstance(keep_val, str) else str(keep_val)
        code = f"df = df.drop_duplicates(keep={keep_param_str})"
        
        op = Operation(
            type="duplicates",
            params={"keep": keep.value},
            generated_code=code,
            description=f"Removed duplicate rows (keep: {keep.value})"
        )
        
        # Update Session
        session.update_dataframe(df_cleaned)
        session.add_operation(op, affected_rows=len(df) - len(df_cleaned))

    @staticmethod
    def replay_remove(df: pd.DataFrame, keep: str) -> pd.DataFrame:
        """Helper to replay duplicate removal on a dataframe (used for Undo/Replay)."""
        keep_val = DuplicateService._get_keep_value(KeepOption(keep))
        return df.drop_duplicates(keep=keep_val)

    @staticmethod
    def _get_keep_value(keep: KeepOption) -> Any:
        """Map enum to pandas keep argument."""
        if keep == KeepOption.NONE:
            return False
        return keep.value
