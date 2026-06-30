"""
ML-specific dataset profiler that extracts features for the recommendation engine.
Leverages the existing app.core.profiler.DatasetProfiler for column classification.
Caches profiles per session ID.
"""
import logging
from typing import Optional, Dict

import numpy as np
import pandas as pd

from app.core.profiler import DatasetProfiler as CoreProfiler
from app.ml.schemas.dataset_profile_schema import DatasetProfile

logger = logging.getLogger(__name__)

# Session-level profile cache
_profile_cache: Dict[str, DatasetProfile] = {}


def clear_cache(session_id: Optional[str] = None) -> None:
    """Clear profile cache for a session or all sessions."""
    if session_id:
        _profile_cache.pop(session_id, None)
    else:
        _profile_cache.clear()


def profile_dataset(
    df: pd.DataFrame,
    session_id: str,
    target_column: Optional[str] = None,
    problem_type: Optional[str] = None,
    goal: Optional[str] = None,
    use_cache: bool = True
) -> DatasetProfile:
    """
    Extract ML-specific features from a DataFrame for the recommendation engine.

    Args:
        df: The dataset DataFrame.
        session_id: Session identifier for caching.
        target_column: Optional target column name.
        problem_type: Optional explicit problem type. Auto-detected if not provided.
        goal: Optional natural language goal from the user.
        use_cache: Whether to use/store cached profiles.

    Returns:
        DatasetProfile with all extracted features.
    """
    # Check cache
    if use_cache and session_id in _profile_cache:
        cached = _profile_cache[session_id]
        # If target/problem type changed, recompute
        if cached.target_column == target_column and (problem_type is None or cached.problem_type == problem_type):
            logger.info(f"Using cached profile for session {session_id}")
            return cached

    logger.info(f"Profiling dataset for session {session_id}...")

    # Use existing core profiler for column classification
    core = CoreProfiler(df)

    row_count = len(df)
    column_count = len(df.columns)
    numeric_count = len(core.numeric_columns)
    categorical_count = len(core.categorical_columns)
    datetime_count = len(core.datetime_columns)
    binary_count = len(core.binary_columns)

    # Ratios
    total_cols = max(column_count, 1)
    numeric_ratio = round(numeric_count / total_cols, 4)
    categorical_ratio = round(categorical_count / total_cols, 4)
    dimensionality_ratio = round(column_count / max(row_count, 1), 6)

    # Missing ratio (total missing cells / total cells)
    total_cells = max(row_count * column_count, 1)
    missing_cells = int(df.isna().sum().sum())
    missing_ratio = round(missing_cells / total_cells, 4)

    # Outlier ratio (using IQR on numeric columns)
    outlier_count = 0
    total_numeric_values = 0
    for col in core.numeric_columns:
        series = df[col].dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count += int(((series < lower) | (series > upper)).sum())
        total_numeric_values += len(series)

    outlier_ratio = round(outlier_count / max(total_numeric_values, 1), 4)

    # Detect problem type and class balance
    detected_problem_type = problem_type
    class_balance = None

    if target_column and target_column in df.columns:
        target_series = df[target_column].dropna()
        unique_count = target_series.nunique()

        if not detected_problem_type:
            # Auto-detect
            if pd.api.types.is_numeric_dtype(target_series) and unique_count > 20:
                detected_problem_type = "regression"
            elif unique_count <= 20:
                detected_problem_type = "classification"
            else:
                detected_problem_type = "classification"

        # Class balance for classification
        if detected_problem_type == "classification" and unique_count >= 2:
            value_counts = target_series.value_counts()
            minority = value_counts.min()
            majority = value_counts.max()
            class_balance = round(minority / max(majority, 1), 4)
    elif not detected_problem_type:
        # No target specified — default to clustering
        detected_problem_type = "clustering"

    # Build natural language feature description for SBERT
    feature_description = _build_feature_description(
        row_count=row_count,
        column_count=column_count,
        numeric_ratio=numeric_ratio,
        categorical_ratio=categorical_ratio,
        missing_ratio=missing_ratio,
        outlier_ratio=outlier_ratio,
        target_column=target_column,
        problem_type=detected_problem_type,
        class_balance=class_balance,
        high_cardinality_columns=core.high_cardinality_columns,
        goal=goal
    )

    profile = DatasetProfile(
        session_id=session_id,
        row_count=row_count,
        column_count=column_count,
        numeric_count=numeric_count,
        categorical_count=categorical_count,
        datetime_count=datetime_count,
        binary_count=binary_count,
        numeric_ratio=numeric_ratio,
        categorical_ratio=categorical_ratio,
        missing_ratio=missing_ratio,
        outlier_ratio=outlier_ratio,
        dimensionality_ratio=dimensionality_ratio,
        target_column=target_column,
        problem_type=detected_problem_type,
        class_balance=class_balance,
        high_cardinality_columns=core.high_cardinality_columns,
        numeric_columns=core.numeric_columns,
        categorical_columns=core.categorical_columns,
        feature_description=feature_description
    )

    # Cache the profile
    if use_cache:
        _profile_cache[session_id] = profile

    logger.info(f"Profile complete: {row_count} rows, {column_count} cols, type={detected_problem_type}")
    return profile


def _build_feature_description(
    row_count: int,
    column_count: int,
    numeric_ratio: float,
    categorical_ratio: float,
    missing_ratio: float,
    outlier_ratio: float,
    target_column: Optional[str],
    problem_type: Optional[str],
    class_balance: Optional[float],
    high_cardinality_columns: list,
    goal: Optional[str] = None
) -> str:
    """Build a natural language description of the dataset for SBERT embedding."""
    parts = []

    # Goal if provided
    if goal:
        parts.append(f"Goal: {goal}.")

    parts.append(f"Tabular dataset with {row_count} rows and {column_count} columns.")

    # Type
    if problem_type and target_column:
        parts.append(f"{problem_type.replace('_', ' ').title()} task targeting '{target_column}'.")
    elif problem_type:
        parts.append(f"{problem_type.replace('_', ' ').title()} task.")

    # Composition
    parts.append(f"{int(numeric_ratio * 100)}% numeric features, {int(categorical_ratio * 100)}% categorical features.")

    # Data quality
    if missing_ratio > 0.2:
        parts.append("High missing value ratio.")
    elif missing_ratio > 0.05:
        parts.append("Moderate missing value ratio.")
    else:
        parts.append("Low missing value ratio.")

    if outlier_ratio > 0.1:
        parts.append("High outlier ratio.")
    elif outlier_ratio > 0.03:
        parts.append("Moderate outlier ratio.")
    else:
        parts.append("Low outlier ratio.")

    # Class balance
    if class_balance is not None:
        if class_balance < 0.3:
            parts.append("Imbalanced classes.")
        else:
            parts.append("Balanced classes.")

    # High cardinality
    if high_cardinality_columns:
        parts.append(f"High cardinality columns: {', '.join(high_cardinality_columns[:5])}.")

    # Size characteristics
    if row_count < 500:
        parts.append("Small dataset.")
    elif row_count < 10000:
        parts.append("Medium-sized dataset.")
    else:
        parts.append("Large dataset.")

    return " ".join(parts)
