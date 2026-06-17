import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.models.session_model import SessionState
from app.models.operation_model import Operation
from app.config.constants import MissingStrategy
from app.exceptions.dataset_exceptions import ColumnNotFound, OperationError
from app.utils.validators import validate_columns_exist
from app.schemas.missing_schema import MissingPreviewResponse

class MissingService:
    """
    Service responsible for handling missing value preview and imputation.
    """
    @staticmethod
    def preview_imputation(session: SessionState, column: str, strategy: MissingStrategy, constant_value: Optional[Any] = None) -> MissingPreviewResponse:
        """
        Preview imputation effects on rows containing missing values.
        """
        df = session.current_df
        validate_columns_exist(df, [column])
        
        null_mask = df[column].isna()
        null_rows = df[null_mask]
        affected_count = len(null_rows)
        
        if affected_count == 0:
            return MissingPreviewResponse(affected_rows=0, sample_before=[], sample_after=[])
            
        # Select first 10 rows with missing values
        sample_rows_indices = null_rows.head(10).index
        sample_before = df.loc[sample_rows_indices].replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        
        # Apply transformation to a temp DataFrame copy to build sample_after
        df_temp = df.loc[sample_rows_indices].copy()
        imputed_val = MissingService._calculate_impute_value(df[column], strategy, constant_value)
        
        if strategy == MissingStrategy.DROP:
            # For drop, the preview shows the sample after drop (which would be empty or remaining rows)
            # Standard output is empty list for drop since the rows are gone, or we can show them removed.
            # Let's return empty lists or show that they were removed.
            sample_after = []
        else:
            df_temp[column] = df_temp[column].fillna(imputed_val)
            sample_after = df_temp.replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
            
        return MissingPreviewResponse(
            affected_rows=affected_count,
            sample_before=sample_before,
            sample_after=sample_after
        )

    @staticmethod
    def apply_imputation(session: SessionState, column: str, strategy: MissingStrategy, constant_value: Optional[Any] = None) -> None:
        """
        Apply imputation or removal of missing values, record operation, and update session.
        """
        df = session.current_df.copy()
        validate_columns_exist(df, [column])
        
        imputed_val = MissingService._calculate_impute_value(df[column], strategy, constant_value)
        
        # Generated code string
        if strategy == MissingStrategy.MEAN:
            code = f"df['{column}'] = df['{column}'].fillna(df['{column}'].mean())"
            df[column] = df[column].fillna(imputed_val)
        elif strategy == MissingStrategy.MEDIAN:
            code = f"df['{column}'] = df['{column}'].fillna(df['{column}'].median())"
            df[column] = df[column].fillna(imputed_val)
        elif strategy == MissingStrategy.MODE:
            code = f"df['{column}'] = df['{column}'].fillna(df['{column}'].mode()[0])"
            df[column] = df[column].fillna(imputed_val)
        elif strategy == MissingStrategy.CONSTANT:
            repr_val = f"'{constant_value}'" if isinstance(constant_value, str) else str(constant_value)
            code = f"df['{column}'] = df['{column}'].fillna({repr_val})"
            df[column] = df[column].fillna(imputed_val)
        elif strategy == MissingStrategy.DROP:
            code = f"df.dropna(subset=['{column}'], inplace=True)"
            df = df.dropna(subset=[column])
        else:
            raise OperationError("Imputation", f"Unsupported imputation strategy: {strategy}")
            
        op = Operation(
            type="missing",
            params={
                "column": column,
                "strategy": strategy.value,
                "constant_value": constant_value
            },
            generated_code=code,
            description=f"Applied {strategy.value} imputation on column '{column}'" if strategy.value != "drop" else f"Dropped missing values in column '{column}'"
        )
        
        session.update_dataframe(df)
        session.operations.append(op)

    @staticmethod
    def replay_missing(df: pd.DataFrame, column: str, strategy: str, constant_value: Optional[Any] = None) -> pd.DataFrame:
        """Replay missing value operation on dataframe."""
        df_copy = df.copy()
        strat = MissingStrategy(strategy)
        imputed_val = MissingService._calculate_impute_value(df_copy[column], strat, constant_value)
        
        if strat == MissingStrategy.DROP:
            return df_copy.dropna(subset=[column])
        else:
            df_copy[column] = df_copy[column].fillna(imputed_val)
            return df_copy

    @staticmethod
    def _calculate_impute_value(series: pd.Series, strategy: MissingStrategy, constant_value: Optional[Any] = None) -> Any:
        """Compute the fill value based on strategy."""
        if strategy == MissingStrategy.MEAN:
            if not pd.api.types.is_numeric_dtype(series):
                raise OperationError("Mean Imputation", "Mean can only be applied to numerical columns.")
            return series.mean()
            
        elif strategy == MissingStrategy.MEDIAN:
            if not pd.api.types.is_numeric_dtype(series):
                raise OperationError("Median Imputation", "Median can only be applied to numerical columns.")
            return series.median()
            
        elif strategy == MissingStrategy.MODE:
            modes = series.mode()
            if modes.empty:
                return None
            return modes[0]
            
        elif strategy == MissingStrategy.CONSTANT:
            if constant_value is None:
                raise OperationError("Constant Imputation", "Constant strategy requires a non-null constant_value.")
            # Coerce type if column is numeric
            if pd.api.types.is_integer_dtype(series):
                try:
                    return int(constant_value)
                except ValueError:
                    raise OperationError("Constant Imputation", f"Value '{constant_value}' is not convertible to integer.")
            elif pd.api.types.is_float_dtype(series):
                try:
                    return float(constant_value)
                except ValueError:
                    raise OperationError("Constant Imputation", f"Value '{constant_value}' is not convertible to float.")
            return constant_value
            
        elif strategy == MissingStrategy.DROP:
            return None
            
        else:
            raise OperationError("Imputation", f"Unknown imputation strategy: {strategy}")
