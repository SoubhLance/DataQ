from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/visualization", tags=["Visualizations"])

@router.get("/missing/{session_id}")
async def get_missing_heatmap(
    max_rows: int = Query(150, description="Maximum number of rows to return in the sample to avoid bloating UI response."),
    session: SessionState = Depends(get_session)
):
    """
    Get matrix structure representing missingness density suitable for heatmaps.
    Returns: List of rows, where each row is a dict of column indicators (0=present, 1=missing).
    """
    return StatisticsService.get_missing_heatmap_data(session, max_rows)

@router.get("/correlation/{session_id}")
async def get_correlation_heatmap(session: SessionState = Depends(get_session)):
    """
    Get coordinate-mapped Pearson correlation coefficients for all numerical variables.
    Returns list of dicts: `[{"x": "col1", "y": "col2", "value": 0.85}, ...]`
    """
    return StatisticsService.get_correlation_heatmap_data(session)

@router.get("/distribution/{session_id}")
async def get_column_distribution(
    column: str = Query(..., description="Numeric column name to calculate histogram bins for."),
    bins: int = Query(10, ge=2, le=100, description="Number of histogram bins."),
    session: SessionState = Depends(get_session)
):
    """
    Get histogram frequency bins and counts for a numerical column.
    """
    return StatisticsService.get_distribution_histogram_data(session, column, bins)

@router.get("/boxplot/{session_id}")
async def get_column_boxplot_stats(
    column: str = Query(..., description="Numeric column name to compute boxplot statistics for."),
    session: SessionState = Depends(get_session)
):
    """
    Get five-number summaries (min, Q1, median, Q3, max), whisker boundaries, and outlier lists.
    """
    return StatisticsService.get_boxplot_data(session, column)
