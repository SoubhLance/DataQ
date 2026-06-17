import pandas as pd
from typing import List, Dict, Any
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from app.models.session_model import SessionState
from app.models.operation_model import Operation
from app.config.constants import ScalingMethod
from app.exceptions.dataset_exceptions import ColumnNotFound, OperationError
from app.utils.validators import validate_columns_exist
from app.schemas.scaling_schema import ScalingPreviewResponse

class ScalingService:
    """
    Service responsible for applying StandardScaler, MinMaxScaler, and RobustScaler.
    """
    @staticmethod
    def preview_scaling(session: SessionState, columns: List[str], method: ScalingMethod) -> ScalingPreviewResponse:
        """
        Preview scaling changes on the first 10 rows.
        """
        df = session.current_df
        validate_columns_exist(df, columns)
        
        # Ensure all columns are numeric
        for col in columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise OperationError("Scaling Preview", f"Column '{col}' is not numeric and cannot be scaled.")
                
        df_temp = df.head(10).copy()
        affected_count = len(df)
        
        sample_before = df_temp[columns].replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        
        scaler = ScalingService._get_scaler(method)
        # Fit transform on copy
        df_temp[columns] = scaler.fit_transform(df_temp[columns])
        
        sample_after = df_temp[columns].replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        
        return ScalingPreviewResponse(
            affected_rows=affected_count,
            sample_before=sample_before,
            sample_after=sample_after
        )

    @staticmethod
    def apply_scaling(session: SessionState, columns: List[str], method: ScalingMethod) -> None:
        """
        Scale columns, generate the code snippet, and update session.
        """
        df = session.current_df.copy()
        validate_columns_exist(df, columns)
        
        # Verify numeric
        for col in columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise OperationError("Scaling", f"Column '{col}' is not numeric and cannot be scaled.")
                
        scaler = ScalingService._get_scaler(method)
        # Apply scaling
        df[columns] = scaler.fit_transform(df[columns])
        
        # Generate code snippet
        scaler_class_name = scaler.__class__.__name__
        code = (
            f"from sklearn.preprocessing import {scaler_class_name}\n"
            f"scaler = {scaler_class_name}()\n"
            f"df[{columns}] = scaler.fit_transform(df[{columns}])"
        )
        
        op = Operation(
            type="scaling",
            params={"columns": columns, "method": method.value},
            generated_code=code,
            description=f"Applied {method.value} scaling on columns: {', '.join(columns)}"
        )
        
        session.update_dataframe(df)
        session.operations.append(op)

    @staticmethod
    def replay_scaling(df: pd.DataFrame, columns: List[str], method: str) -> pd.DataFrame:
        """Replay scaling operation on a dataframe."""
        df_copy = df.copy()
        meth = ScalingMethod(method)
        scaler = ScalingService._get_scaler(meth)
        df_copy[columns] = scaler.fit_transform(df_copy[columns])
        return df_copy

    @staticmethod
    def _get_scaler(method: ScalingMethod) -> Any:
        """Helper to retrieve sklearn scaler class."""
        if method == ScalingMethod.STANDARD:
            return StandardScaler()
        elif method == ScalingMethod.MINMAX:
            return MinMaxScaler()
        elif method == ScalingMethod.ROBUST:
            return RobustScaler()
        else:
            raise OperationError("Scaling", f"Unsupported scaling method: {method}")
