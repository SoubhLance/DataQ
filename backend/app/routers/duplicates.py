from fastapi import APIRouter, Depends
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.schemas.duplicate_schema import DuplicateDetectResponse, DuplicateRemoveRequest, DuplicatePreviewResponse
from app.services.duplicate_service import DuplicateService

router = APIRouter(prefix="/duplicates", tags=["Duplicates"])

@router.get("/{session_id}", response_model=DuplicateDetectResponse)
async def check_duplicates(session: SessionState = Depends(get_session)):
    """
    Get duplicate rows statistics.
    """
    return DuplicateService.detect_duplicates(session)

@router.post("/preview", response_model=DuplicatePreviewResponse)
async def preview_duplicate_removal(
    request: DuplicateRemoveRequest
):
    """
    Preview dataset change before applying duplicate removal.
    """
    # Verify session matching request
    session = get_session(request.session_id)
    return DuplicateService.preview_remove(session, request.keep)

@router.post("/remove")
async def remove_duplicates(
    request: DuplicateRemoveRequest
):
    """
    Remove duplicate rows and register the action in pipeline history.
    """
    session = get_session(request.session_id)
    DuplicateService.apply_remove(session, request.keep)
    return {
        "status": "success",
        "message": "Duplicate rows removed successfully.",
        "rows_remaining": session.rows
    }
