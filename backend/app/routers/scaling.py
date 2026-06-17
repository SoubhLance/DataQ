from fastapi import APIRouter, Depends
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.schemas.scaling_schema import ScalingRequest, ScalingPreviewResponse
from app.services.scaling_service import ScalingService

router = APIRouter(prefix="/scaling", tags=["Scaling"])

@router.post("/preview", response_model=ScalingPreviewResponse)
async def preview_scaling(
    request: ScalingRequest
):
    """
    Preview the effect of scaling (Standard, MinMax, Robust) on the selected numerical columns.
    """
    session = get_session(request.session_id)
    return ScalingService.preview_scaling(session, request.columns, request.method)

@router.post("/apply")
async def apply_scaling(
    request: ScalingRequest
):
    """
    Apply feature scaling (Standard, MinMax, Robust) on selected columns and register in history.
    """
    session = get_session(request.session_id)
    ScalingService.apply_scaling(session, request.columns, request.method)
    return {
        "status": "success",
        "message": f"Successfully applied '{request.method.value}' scaling to columns: {request.columns}."
    }
