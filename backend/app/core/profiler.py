import pandas as pd
from typing import List

class DatasetProfiler:
    """
    Profile a Pandas DataFrame to identify column types, cardinality,
    and metadata for automated preprocessing recommendations.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.total_rows = len(df)
        self.columns = list(df.columns)
        
        self.numeric_columns = self._get_numeric_columns()
        self.categorical_columns = self._get_categorical_columns()
        self.datetime_columns = self._get_datetime_columns()
        self.binary_columns = self._get_binary_columns()
        self.high_cardinality_columns = self._get_high_cardinality_columns()
        self.target_candidates = self._get_target_candidates()

    def _get_numeric_columns(self) -> List[str]:
        """Return names of columns with numeric data types."""
        cols = []
        for col in self.columns:
            if pd.api.types.is_numeric_dtype(self.df[col]) and not pd.api.types.is_bool_dtype(self.df[col]):
                cols.append(col)
        return cols

    def _get_categorical_columns(self) -> List[str]:
        """Return names of columns with string, object, or category types."""
        cols = []
        for col in self.columns:
            # Check object, string, or category, excluding numeric and datetime
            if (pd.api.types.is_object_dtype(self.df[col]) or 
                isinstance(self.df[col].dtype, pd.CategoricalDtype) or
                isinstance(self.df[col].dtype, pd.StringDtype)) and not self._is_datetime_col(col):
                cols.append(col)
        return cols

    def _get_datetime_columns(self) -> List[str]:
        """Return names of columns with datetime types."""
        cols = []
        for col in self.columns:
            if self._is_datetime_col(col):
                cols.append(col)
        return cols

    def _is_datetime_col(self, col: str) -> bool:
        """Helper to determine if a column is of datetime type or resembles it."""
        if pd.api.types.is_datetime64_any_dtype(self.df[col]):
            return True
        # Try to inspect string values if they look like dates
        if pd.api.types.is_object_dtype(self.df[col]) or isinstance(self.df[col].dtype, pd.StringDtype):
            sample = self.df[col].dropna().head(5)
            if sample.empty:
                return False
            try:
                # If we can parse the sample values successfully, classify it
                pd.to_datetime(sample, errors='raise', format='mixed')
                return True
            except (ValueError, TypeError, OverflowError):
                return False
        return False

    def _get_binary_columns(self) -> List[str]:
        """Return names of columns with exactly two unique values (ignoring nulls)."""
        cols = []
        for col in self.columns:
            non_null_unique = self.df[col].nunique(dropna=True)
            if non_null_unique == 2:
                cols.append(col)
        return cols

    def _get_high_cardinality_columns(self) -> List[str]:
        """
        Return names of categorical columns with high cardinality
        (e.g., unique values > 10% of total rows and total unique > 10).
        """
        cols = []
        for col in self.categorical_columns:
            unique_count = self.df[col].nunique(dropna=True)
            if self.total_rows > 0:
                ratio = unique_count / self.total_rows
                if unique_count > 10 and ratio > 0.10:
                    cols.append(col)
            elif unique_count > 10:
                cols.append(col)
        return cols

    def _get_target_candidates(self) -> List[str]:
        """
        Identify columns that are suitable candidates for machine learning targets
        (e.g. contains names like 'class', 'label', 'target', or has low cardinality).
        """
        candidates = []
        target_keywords = {"target", "label", "class", "survived", "y", "output", "churn"}
        
        for col in self.columns:
            # Low unique counts (e.g. classification target) or specific keywords
            col_lower = col.lower()
            unique_count = self.df[col].nunique(dropna=True)
            
            # Match keywords
            has_keyword = any(kw in col_lower for kw in target_keywords)
            
            # Avoid columns that look like IDs (high unique count string columns)
            is_id_like = (col_lower == "id" or col_lower.endswith("_id")) and unique_count > 100
            
            if (has_keyword or (unique_count >= 2 and unique_count <= 20)) and not is_id_like:
                candidates.append(col)
                
        return candidates
