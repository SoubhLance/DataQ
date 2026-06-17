import pandas as pd
from typing import List
from app.models.session_model import SessionState
from app.core.profiler import DatasetProfiler
from app.schemas.dataset_schema import InspectResponse, ColumnInspect

class InspectService:
    """
    Service responsible for inspecting the basic structural metadata of the dataset.
    """
    @staticmethod
    def inspect_dataset(session: SessionState) -> InspectResponse:
        """
        Inspect dataset to extract shape, data types, memory usage, and basic column list.
        """
        df = session.current_df
        profiler = DatasetProfiler(df)
        
        # Calculate memory usage in MB
        memory_usage_mb = float(df.memory_usage(deep=True).sum() / (1024 * 1024))
        
        columns_inspect: List[ColumnInspect] = []
        total_rows = len(df)
        
        for col in df.columns:
            # Check basic metrics
            missing_count = int(df[col].isna().sum())
            missing_percent = float((missing_count / total_rows) * 100) if total_rows > 0 else 0.0
            unique_count = int(df[col].nunique(dropna=True))
            cardinality = float(unique_count / total_rows) if total_rows > 0 else 0.0
            
            columns_inspect.append(
                ColumnInspect(
                    name=str(col),
                    dtype=str(df[col].dtype),
                    missing=missing_count,
                    missing_percent=round(missing_percent, 2),
                    unique=unique_count,
                    cardinality=round(cardinality, 4)
                )
            )
            
        return InspectResponse(
            shape=[total_rows, len(df.columns)],
            columns=columns_inspect,
            numeric_columns=profiler.numeric_columns,
            categorical_columns=profiler.categorical_columns,
            memory_usage_mb=round(memory_usage_mb, 2)
        )
