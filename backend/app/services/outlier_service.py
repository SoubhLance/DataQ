import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from app.models.session_model import SessionState
from app.models.operation_model import Operation
from app.config.constants import OutlierMethod, OutlierAction
from app.exceptions.dataset_exceptions import ColumnNotFound, OperationError
from app.utils.validators import validate_columns_exist
from app.schemas.outlier_schema import OutlierCheckResponse, OutlierColumnDetail, OutlierPreviewResponse
from app.core.profiler import DatasetProfiler

class OutlierService:
    """
    Service responsible for outlier detection, previews, and treatment.
    """
    @staticmethod
    def detect_outliers(session: SessionState, method: OutlierMethod, threshold: float = 3.0, contamination: float = 0.05) -> OutlierCheckResponse:
        """
        Scan all numerical columns and detect outlier statistics.
        """
        df = session.current_df
        profiler = DatasetProfiler(df)
        details = []
        
        for col in profiler.numeric_columns:
            series = df[col].dropna()
            if len(series) < 5:  # Too few values to detect outliers
                continue
                
            outlier_mask, lower, upper = OutlierService._get_outlier_mask_and_bounds(series, method, threshold, contamination)
            outlier_count = int(outlier_mask.sum())
            percentage = (outlier_count / len(df)) * 100 if len(df) > 0 else 0.0
            
            details.append(
                OutlierColumnDetail(
                    column=col,
                    outliers=outlier_count,
                    percentage=round(percentage, 2),
                    lower_bound=round(float(lower), 3) if lower is not None else None,
                    upper_bound=round(float(upper), 3) if upper is not None else None
                )
            )
            
        return OutlierCheckResponse(
            method=method,
            columns=details
        )

    @staticmethod
    def preview_treatment(session: SessionState, column: str, method: OutlierMethod, action: OutlierAction, threshold: float = 3.0, contamination: float = 0.05) -> OutlierPreviewResponse:
        """
        Preview how outlier treatment affects rows containing outliers in the specified column.
        """
        df = session.current_df
        validate_columns_exist(df, [column])
        
        series = df[column]
        series_clean = series.dropna()
        if len(series_clean) < 5:
            return OutlierPreviewResponse(affected_rows=0, sample_before=[], sample_after=[])
            
        outlier_mask_clean, lower, upper = OutlierService._get_outlier_mask_and_bounds(series_clean, method, threshold, contamination)
        
        # Map outlier mask back to original series including nulls
        outlier_mask = pd.Series(False, index=df.index)
        outlier_mask.loc[series_clean.index] = outlier_mask_clean
        
        outlier_rows = df[outlier_mask]
        affected_count = len(outlier_rows)
        
        if affected_count == 0:
            return OutlierPreviewResponse(affected_rows=0, sample_before=[], sample_after=[])
            
        # Select first 10 rows with outliers
        sample_rows_indices = outlier_rows.head(10).index
        sample_before = df.loc[sample_rows_indices].replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        
        # Build preview of treated sample
        df_temp = df.loc[sample_rows_indices].copy()
        
        if action == OutlierAction.REMOVE:
            sample_after = [] # These rows are deleted
        elif action == OutlierAction.CAP:
            if lower is not None and upper is not None:
                df_temp[column] = df_temp[column].clip(lower=lower, upper=upper)
            sample_after = df_temp.replace({pd.NA: None, float('nan'): None}).to_dict(orient="records")
        else: # KEEP
            sample_after = sample_before
            
        return OutlierPreviewResponse(
            affected_rows=affected_count,
            sample_before=sample_before,
            sample_after=sample_after
        )

    @staticmethod
    def apply_treatment(session: SessionState, column: str, method: OutlierMethod, action: OutlierAction, threshold: float = 3.0, contamination: float = 0.05) -> None:
        """
        Apply outlier treatment, write generated code snippet, and update session.
        """
        df = session.current_df.copy()
        validate_columns_exist(df, [column])
        
        series = df[column]
        series_clean = series.dropna()
        
        if len(series_clean) >= 5:
            outlier_mask_clean, lower, upper = OutlierService._get_outlier_mask_and_bounds(series_clean, method, threshold, contamination)
            
            # Map mask
            outlier_mask = pd.Series(False, index=df.index)
            outlier_mask.loc[series_clean.index] = outlier_mask_clean
            
            # Action application & Code generation
            code_parts = []
            if method == OutlierMethod.IQR:
                code_parts = [
                    f"Q1 = df['{column}'].quantile(0.25)",
                    f"Q3 = df['{column}'].quantile(0.75)",
                    f"IQR = Q3 - Q1",
                    f"lower = Q1 - 1.5 * IQR",
                    f"upper = Q3 + 1.5 * IQR"
                ]
                if action == OutlierAction.REMOVE:
                    code_parts.append(f"df = df[(df['{column}'] >= lower) & (df['{column}'] <= upper) | df['{column}'].isna()]")
                    # Do not drop null values during outlier removal unless explicitly requested
                    df = df[~outlier_mask]
                elif action == OutlierAction.CAP:
                    code_parts.append(f"df['{column}'] = df['{column}'].clip(lower=lower, upper=upper)")
                    df[column] = df[column].clip(lower=lower, upper=upper)
                    
            elif method == OutlierMethod.ZSCORE:
                code_parts = [
                    f"mean = df['{column}'].mean()",
                    f"std = df['{column}'].std()",
                    f"lower = mean - {threshold} * std",
                    f"upper = mean + {threshold} * std"
                ]
                if action == OutlierAction.REMOVE:
                    code_parts.append(f"df = df[(df['{column}'] >= lower) & (df['{column}'] <= upper) | df['{column}'].isna()]")
                    df = df[~outlier_mask]
                elif action == OutlierAction.CAP:
                    code_parts.append(f"df['{column}'] = df['{column}'].clip(lower=lower, upper=upper)")
                    df[column] = df[column].clip(lower=lower, upper=upper)
                    
            elif method == OutlierMethod.ISOLATION_FOREST:
                code_parts = [
                    f"from sklearn.ensemble import IsolationForest",
                    f"iforest = IsolationForest(contamination={contamination}, random_state=42)",
                    f"# Identify outliers (excluding missing values)",
                    f"vals = df['{column}'].dropna().values.reshape(-1, 1)",
                    f"if len(vals) >= 5:",
                    f"    preds = iforest.fit_predict(vals)",
                    f"    outlier_idx = df['{column}'].dropna().index[preds == -1]"
                ]
                if action == OutlierAction.REMOVE:
                    code_parts.append(f"    df = df.drop(outlier_idx)")
                    df = df[~outlier_mask]
                elif action == OutlierAction.CAP:
                    # For capping, we cap to min/max of non-outliers
                    code_parts.extend([
                        f"    non_outlier_vals = df['{column}'].dropna()[preds == 1]",
                        f"    lower = non_outlier_vals.min() if len(non_outlier_vals) > 0 else None",
                        f"    upper = non_outlier_vals.max() if len(non_outlier_vals) > 0 else None",
                        f"    if lower is not None and upper is not None:",
                        f"        df['{column}'] = df['{column}'].clip(lower=lower, upper=upper)"
                    ])
                    if lower is not None and upper is not None:
                        df[column] = df[column].clip(lower=lower, upper=upper)
                        
            generated_code = "\n".join(code_parts) if action != OutlierAction.KEEP else f"# Outliers in '{column}' were kept intact."
        else:
            generated_code = f"# Column '{column}' had too few values for outlier treatment."
            
        op = Operation(
            type="outliers",
            params={
                "column": column,
                "method": method.value,
                "action": action.value,
                "threshold": threshold,
                "contamination": contamination
            },
            generated_code=generated_code,
            description=f"Applied outlier treatment ({action.value}) on column '{column}' via {method.value}"
        )
        
        affected_rows = int(outlier_mask.sum()) if len(series_clean) >= 5 else 0
        session.update_dataframe(df)
        session.add_operation(op, affected_rows=affected_rows)

    @staticmethod
    def replay_outliers(df: pd.DataFrame, column: str, method: str, action: str, threshold: float = 3.0, contamination: float = 0.05) -> pd.DataFrame:
        """Replay outlier operation on a dataframe."""
        df_copy = df.copy()
        series = df_copy[column]
        series_clean = series.dropna()
        if len(series_clean) < 5:
            return df_copy
            
        meth = OutlierMethod(method)
        act = OutlierAction(action)
        
        outlier_mask_clean, lower, upper = OutlierService._get_outlier_mask_and_bounds(series_clean, meth, threshold, contamination)
        
        outlier_mask = pd.Series(False, index=df_copy.index)
        outlier_mask.loc[series_clean.index] = outlier_mask_clean
        
        if act == OutlierAction.REMOVE:
            df_copy = df_copy[~outlier_mask]
        elif act == OutlierAction.CAP:
            if lower is not None and upper is not None:
                df_copy[column] = df_copy[column].clip(lower=lower, upper=upper)
                
        return df_copy

    @staticmethod
    def _get_outlier_mask_and_bounds(series: pd.Series, method: OutlierMethod, threshold: float = 3.0, contamination: float = 0.05) -> Tuple[pd.Series, Optional[float], Optional[float]]:
        """
        Helper returning a boolean mask of outlier indices (matching the input series index)
        and the lower/upper bounds.
        """
        if method == OutlierMethod.IQR:
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            mask = (series < lower) | (series > upper)
            return mask, float(lower), float(upper)
            
        elif method == OutlierMethod.ZSCORE:
            mean = series.mean()
            std = series.std()
            if std > 0:
                z_scores = (series - mean) / std
                mask = z_scores.abs() > threshold
                lower = mean - threshold * std
                upper = mean + threshold * std
                return mask, float(lower), float(upper)
            else:
                return pd.Series(False, index=series.index), None, None
                
        elif method == OutlierMethod.ISOLATION_FOREST:
            vals = series.values.reshape(-1, 1)
            iforest = IsolationForest(contamination=contamination, random_state=42)
            preds = iforest.fit_predict(vals)
            mask_clean = preds == -1
            
            # Construct bounds based on non-outliers
            non_outliers = series[preds == 1]
            lower = non_outliers.min() if len(non_outliers) > 0 else None
            upper = non_outliers.max() if len(non_outliers) > 0 else None
            
            return pd.Series(mask_clean, index=series.index), lower, upper
            
        return pd.Series(False, index=series.index), None, None
