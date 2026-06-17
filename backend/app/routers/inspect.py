from fastapi import APIRouter, Depends, Query
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.schemas.dataset_schema import InspectResponse, QualityResponse, CorrelationResponse, ImbalanceResponse
from app.services.inspect_service import InspectService
from app.services.statistics_service import StatisticsService

router = APIRouter(tags=["Inspection"])

@router.get("/inspect/{session_id}", response_model=InspectResponse)
async def inspect_dataset(session: SessionState = Depends(get_session)):
    """
    Get basic structural details (shape, dtypes, column list, memory usage).
    """
    return InspectService.inspect_dataset(session)

@router.get("/quality/{session_id}", response_model=QualityResponse)
async def get_dataset_quality_score(session: SessionState = Depends(get_session)):
    """
    Calculate dataset quality score out of 100 with list of warning items.
    """
    return StatisticsService.calculate_quality_score(session)

@router.get("/correlation/{session_id}", response_model=CorrelationResponse)
async def get_correlation_matrix(
    threshold: float = Query(0.9, ge=0.0, le=1.0, description="Pearson coefficient threshold to tag highly correlated columns."),
    session: SessionState = Depends(get_session)
):
    """
    Compute Pearson correlation matrix and identify highly correlated column pairs.
    """
    return StatisticsService.calculate_correlation_matrix(session, threshold)

@router.get("/imbalance/{session_id}", response_model=ImbalanceResponse)
async def get_class_imbalance(
    target: str = Query(..., description="Target column to assess class imbalance."),
    session: SessionState = Depends(get_session)
):
    """
    Determine class distribution ratio and skewness for machine learning target columns.
    """
    return StatisticsService.check_class_imbalance(session, target)

@router.get("/sample/{session_id}")
async def get_dataframe_sample(
    limit: int = Query(20, ge=1, le=100, description="Number of sample rows to return."),
    session: SessionState = Depends(get_session)
):
    """
    Get a sample of the first N rows of the dataset.
    """
    import pandas as pd
    df = session.current_df
    # Replace pandas NA/NaN with None for clean JSON serialization
    sample_df = df.head(limit).replace({pd.NA: None, float('nan'): None, pd.NaT: None})
    return sample_df.to_dict(orient="records")

