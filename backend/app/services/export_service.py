import os
from app.models.session_model import SessionState
from app.config.settings import settings
from app.utils.file_utils import save_dataframe_to_file
from app.exceptions.dataset_exceptions import OperationError

class ExportService:
    """
    Service responsible for exporting the cleaned dataset to various file formats.
    """
    @staticmethod
    def export_dataset(session: SessionState, format_ext: str = "csv") -> str:
        """
        Export current working dataframe to clean storage and return absolute filepath.
        Supports CSV, XLSX, JSON, Parquet.
        """
        df = session.current_df
        if df.empty:
            raise OperationError("Export", "Cannot export an empty dataset.")
            
        ext = format_ext.lower().strip()
        if not ext.startswith('.'):
            ext = f".{ext}"
            
        filename = f"{session.session_id}_cleaned{ext}"
        filepath = os.path.join(settings.CLEANED_DIR, filename)
        
        # Save dataframe to disk
        save_dataframe_to_file(df, filepath, ext)
        
        return filepath
