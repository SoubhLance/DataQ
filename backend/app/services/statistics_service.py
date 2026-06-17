import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from app.models.session_model import SessionState
from app.core.profiler import DatasetProfiler
from app.schemas.dataset_schema import QualityResponse, CorrelationResponse, ImbalanceResponse
from app.exceptions.dataset_exceptions import ColumnNotFound

class StatisticsService:
    """
    Service responsible for computing complex dataset statistics (correlation,
    skewness, variance, class imbalance, overall quality scores, and visualization-friendly data).
    """
    @staticmethod
    def get_skewness_and_variance(session: SessionState) -> Dict[str, Dict[str, float]]:
        """Calculate skewness and variance for numeric columns."""
        df = session.current_df
        profiler = DatasetProfiler(df)
        stats = {}
        for col in profiler.numeric_columns:
            series = df[col].dropna()
            if not series.empty:
                stats[col] = {
                    "skewness": float(series.skew()),
                    "variance": float(series.var())
                }
            else:
                stats[col] = {
                    "skewness": 0.0,
                    "variance": 0.0
                }
        return stats

    @staticmethod
    def calculate_correlation_matrix(session: SessionState, threshold: float = 0.9) -> CorrelationResponse:
        """
        Compute Pearson correlation matrix and identify highly correlated columns.
        """
        df = session.current_df
        profiler = DatasetProfiler(df)
        numeric_cols = profiler.numeric_columns
        
        if len(df.columns) > 300 or len(numeric_cols) > 300:
            return CorrelationResponse(
                matrix={},
                highly_correlated=[],
                warning=f"Correlation computation skipped: dataset has {len(df.columns)} columns (limit is 300)."
            )
            
        if len(numeric_cols) < 2:
            return CorrelationResponse(matrix={}, highly_correlated=[])
            
        corr_df = df[numeric_cols].corr(method='pearson')
        matrix_dict = corr_df.replace({np.nan: None}).to_dict()
        
        columns = list(corr_df.columns)
        corr_matrix = corr_df.values
        
        # Upper triangle index pairs
        rows, cols = np.triu_indices(len(columns), k=1)
        mask = np.abs(corr_matrix[rows, cols]) >= threshold
        
        matching_rows = rows[mask]
        matching_cols = cols[mask]
        
        highly_correlated = []
        for r, c in zip(matching_rows, matching_cols):
            val = corr_matrix[r, c]
            if pd.notna(val):
                col1 = columns[r]
                col2 = columns[c]
                highly_correlated.append({
                    "column1": col1,
                    "column2": col2,
                    "correlation": round(float(val), 3),
                    "recommendation": f"Pearson coefficient is high ({round(float(val), 2)}). Recommend dropping either '{col1}' or '{col2}'."
                })
                
        return CorrelationResponse(
            matrix=matrix_dict,
            highly_correlated=highly_correlated
        )

    @staticmethod
    def calculate_quality_score(session: SessionState) -> QualityResponse:
        """
        Evaluate dataset quality score out of 100 and compile warning list.
        """
        df = session.current_df
        total_rows = len(df)
        score = 100
        warnings = []
        
        if total_rows == 0:
            return QualityResponse(score=0, warnings=["Empty dataset has a quality score of 0."])
            
        # 1. Duplicates check
        duplicate_count = int(df.duplicated().sum())
        if duplicate_count > 0:
            score -= 10
            warnings.append(f"Dataset contains {duplicate_count} duplicate rows (-10 penalty).")
            
        # 2. Missing values check
        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_pct = (missing_count / total_rows) * 100
            if missing_pct > 20:
                score -= 20
                warnings.append(f"Column '{col}' has {missing_pct:.1f}% missing values (-20 penalty).")
                
        # 3. Outliers check (IQR method on numeric columns)
        profiler = DatasetProfiler(df)
        for col in profiler.numeric_columns:
            series = df[col].dropna()
            if len(series) > 0:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outlier_count = int(((series < lower) | (series > upper)).sum())
                outlier_pct = (outlier_count / total_rows) * 100
                if outlier_pct > 5:
                    score -= 15
                    warnings.append(f"Column '{col}' has {outlier_pct:.1f}% outliers (-15 penalty).")
                    
        # 4. High cardinality check
        for col in profiler.high_cardinality_columns:
            warnings.append(f"Categorical column '{col}' has high cardinality (-10 penalty).")
            score -= 10
            
        score = max(0, score)
        return QualityResponse(score=score, warnings=warnings)

    @staticmethod
    def check_class_imbalance(session: SessionState, target: str) -> ImbalanceResponse:
        """
        Compute class ratios and determine imbalance flag for categorical/binary targets.
        """
        df = session.current_df
        if target not in df.columns:
            raise ColumnNotFound(target)
            
        series = df[target].dropna()
        if series.empty:
            return ImbalanceResponse(ratio="0:0", imbalanced=False, class_counts={})
            
        counts = series.value_counts()
        total = counts.sum()
        counts_dict = {str(k): int(v) for k, v in counts.items()}
        
        percentages = counts / total * 100
        majority_pct = percentages.iloc[0]
        
        ratio_str = f"{round(majority_pct)}:{round(100 - majority_pct)}"
        imbalanced = majority_pct >= 75.0
        
        return ImbalanceResponse(
            ratio=ratio_str,
            imbalanced=imbalanced,
            class_counts=counts_dict
        )

    # --- Visualization Data Generators ---

    @staticmethod
    def get_missing_heatmap_data(session: SessionState, max_sample_rows: int = 150) -> List[Dict[str, Any]]:
        """
        Generates a downsampled matrix indicating missing status (True = missing, False = present)
        suitable for heatmaps.
        """
        df = session.current_df
        total_rows = len(df)
        
        if total_rows > max_sample_rows:
            # Downsample evenly to represent dataset shape accurately
            indices = np.linspace(0, total_rows - 1, max_sample_rows, dtype=int)
            sample_df = df.iloc[indices]
        else:
            sample_df = df
            
        heatmap_data = []
        for i, (idx, row) in enumerate(sample_df.iterrows()):
            row_dict = {"row_index": i}
            for col in df.columns:
                row_dict[col] = int(pd.isna(row[col]))  # 1 for missing, 0 for present
            heatmap_data.append(row_dict)
            
        return heatmap_data

    @staticmethod
    def get_correlation_heatmap_data(session: SessionState) -> List[Dict[str, Any]]:
        """
        Flattens correlation matrix into a coordinate format suitable for Recharts heatmap tiles.
        """
        df = session.current_df
        profiler = DatasetProfiler(df)
        numeric_cols = profiler.numeric_columns
        
        if len(df.columns) > 300 or len(numeric_cols) > 300:
            return []
            
        if len(numeric_cols) < 2:
            return []
            
        corr_df = df[numeric_cols].corr(method='pearson')
        
        flat_data = []
        for col1 in corr_df.columns:
            for col2 in corr_df.columns:
                val = corr_df.loc[col1, col2]
                flat_data.append({
                    "x": col1,
                    "y": col2,
                    "value": round(float(val), 3) if pd.notna(val) else None
                })
                
        return flat_data

    @staticmethod
    def get_distribution_histogram_data(session: SessionState, column: str, bins: int = 10) -> List[Dict[str, Any]]:
        """
        Calculates histogram bins and counts for a numeric column.
        """
        df = session.current_df
        if column not in df.columns:
            raise ColumnNotFound(column)
            
        series = df[column].dropna()
        if series.empty or not pd.api.types.is_numeric_dtype(series):
            return []
            
        counts, bin_edges = np.histogram(series, bins=bins)
        
        histogram_data = []
        for i in range(len(counts)):
            start = float(bin_edges[i])
            end = float(bin_edges[i+1])
            histogram_data.append({
                "bin_start": round(start, 3),
                "bin_end": round(end, 3),
                "bin_label": f"{round(start, 1)}-{round(end, 1)}",
                "count": int(counts[i])
            })
            
        return histogram_data

    @staticmethod
    def get_boxplot_data(session: SessionState, column: str) -> Dict[str, Any]:
        """
        Calculates boxplot statistics (five-number summary + outliers list) for a numeric column.
        """
        df = session.current_df
        if column not in df.columns:
            raise ColumnNotFound(column)
            
        series = df[column].dropna()
        if series.empty or not pd.api.types.is_numeric_dtype(series):
            return {}
            
        q1 = float(series.quantile(0.25))
        median = float(series.median())
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        
        # Calculate actual bounds within whisker range
        min_val = float(series[series >= lower].min()) if not series[series >= lower].empty else float(series.min())
        max_val = float(series[series <= upper].max()) if not series[series <= upper].empty else float(series.max())
        
        outliers_series = series[(series < lower) | (series > upper)]
        # Cap outlier list size for visualization performance
        outliers = outliers_series.head(100).tolist()
        
        return {
            "column": column,
            "min": round(min_val, 3),
            "q1": round(q1, 3),
            "median": round(median, 3),
            "q3": round(q3, 3),
            "max": round(max_val, 3),
            "lower_whisker": round(lower, 3),
            "upper_whisker": round(upper, 3),
            "outliers_count": len(outliers_series),
            "outliers_sample": [round(float(o), 3) for o in outliers]
        }
