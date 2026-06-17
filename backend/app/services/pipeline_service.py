import pandas as pd
from typing import Dict, Any, List
from app.models.session_model import SessionState
from app.models.operation_model import Operation
from app.codegen.pipeline_generator import PipelineGenerator
from app.services.duplicate_service import DuplicateService
from app.services.missing_service import MissingService
from app.services.outlier_service import OutlierService
from app.services.column_service import ColumnService
from app.services.scaling_service import ScalingService
from app.exceptions.dataset_exceptions import OperationError

class PipelineService:
    """
    Service responsible for pipeline orchestration, undo/replay execution,
    and generating code pipelines in various formats.
    """
    
    @staticmethod
    def get_pandas_script(session: SessionState) -> str:
        """Get the full Python pandas cleanup script."""
        return PipelineGenerator.generate_pandas_script(session.filename, session.operations)

    @staticmethod
    def get_sklearn_pipeline(session: SessionState) -> str:
        """Get the Scikit-Learn Pipeline and ColumnTransformer layout."""
        return PipelineGenerator.generate_sklearn_pipeline(session.operations)

    @staticmethod
    def get_jupyter_notebook(session: SessionState) -> str:
        """Get the Jupyter Notebook JSON representation."""
        return PipelineGenerator.generate_jupyter_notebook(session.filename, session.operations)

    @staticmethod
    def get_yaml_recipe(session: SessionState) -> str:
        """Get the YAML formatting recipe list."""
        return PipelineGenerator.generate_yaml_recipe(session.operations)

    @staticmethod
    def undo_last_operation(session: SessionState) -> None:
        """
        Undo the last operation by popping it from the operations history,
        reloading the original dataset, and replaying all remaining operations.
        """
        if not session.operations:
            raise OperationError("Undo", "No operations to undo.")
            
        # Remove the last operation
        session.operations.pop()
        
        # Rebuild state from scratch
        PipelineService.replay_all_operations(session)

    @staticmethod
    def replay_all_operations(session: SessionState) -> None:
        """
        Reload the original dataset and sequentially apply all recorded operations.
        """
        df = session.original_df.copy()
        
        for op in session.operations:
            try:
                df = PipelineService._execute_operation_step(df, op)
            except Exception as e:
                raise OperationError(
                    "Replay", 
                    f"Failed to replay step '{op.type}' with parameters {op.params}. Details: {str(e)}"
                )
                
        # Update current cached DataFrame in session
        session.update_dataframe(df)

    @staticmethod
    def _execute_operation_step(df: pd.DataFrame, op: Operation) -> pd.DataFrame:
        """
        Apply a single operation on a DataFrame by calling the corresponding service.
        """
        op_type = op.type
        params = op.params
        
        if op_type == "duplicates":
            return DuplicateService.replay_remove(df, **params)
            
        elif op_type == "missing":
            return MissingService.replay_missing(df, **params)
            
        elif op_type == "outliers":
            return OutlierService.replay_outliers(df, **params)
            
        elif op_type in ["column_drop", "column_rename", "column_cast", "column_encode"]:
            return ColumnService.replay_column_op(df, op_type, params)
            
        elif op_type == "scaling":
            return ScalingService.replay_scaling(df, **params)
            
        else:
            raise OperationError("Replay Step", f"Unsupported operation type '{op_type}' in history.")
