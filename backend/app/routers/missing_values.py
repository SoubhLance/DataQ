from fastapi import APIRouter, Depends
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.schemas.missing_schema import MissingCheckResponse, MissingApplyRequest, MissingPreviewResponse
from app.services.missing_service import MissingService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/missing", tags=["Missing Values"])

@router.get("/{session_id}", response_model=MissingCheckResponse)
async def check_missing_values(session: SessionState = Depends(get_session)):
    """
    Scan missing values and get suggested strategies for all columns containing null values.
    """
    recs = RecommendationService.get_missing_recommendations(session)
    return MissingCheckResponse(columns=recs)

@router.post("/preview", response_model=MissingPreviewResponse)
async def preview_missing_imputation(
    request: MissingApplyRequest
):
    """
    Preview the effect of applying missing value imputation on null values.
    """
    session = get_session(request.session_id)
    return MissingService.preview_imputation(session, request.column, request.strategy, request.constant_value)

@router.post("/apply")
async def apply_missing_imputation(
    request: MissingApplyRequest
):
    """
    Apply imputation strategy to a column and register the action in pipeline history.
    """
    session = get_session(request.session_id)
    MissingService.apply_imputation(session, request.column, request.strategy, request.constant_value)
    return {
        "status": "success",
        "message": f"Imputation strategy '{request.strategy.value}' successfully applied to column '{request.column}'."
    }
