import logging
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.schemas.outlier_schema import OutlierCheckResponse, OutlierRemoveRequest, OutlierPreviewResponse
from app.services.outlier_service import OutlierService
from app.services.task_service import task_service
from app.config.constants import OutlierMethod

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outliers", tags=["Outliers"])

def run_background_outlier_treatment(session_id: str, column: str, method: OutlierMethod, action: str, threshold: float, contamination: float, task_id: str):
    """Background task runner for outlier treatment."""
    try:
        session = get_session(session_id)
        task_service.update_task_progress(task_id, 30, f"Scanning outliers in column '{column}'...")
        
        # Treatment logic
        task_service.update_task_progress(task_id, 60, f"Applying treatment ({action}) on column '{column}'...")
        OutlierService.apply_treatment(session, column, method, action, threshold, contamination)
        
        task_service.complete_task(task_id, result={
            "status": "success",
            "message": f"Successfully applied outlier treatment: {action} on {column}"
        })
    except Exception as e:
        logger.error(f"Background outlier treatment failed: {str(e)}")
        task_service.fail_task(task_id, str(e))

@router.get("/{session_id}", response_model=OutlierCheckResponse)
async def check_outliers(
    method: OutlierMethod = Query(OutlierMethod.IQR, description="Detection method: 'iqr', 'zscore', 'iforest'."),
    threshold: float = Query(3.0, description="Z-score threshold multiplier (Z-score only)."),
    contamination: float = Query(0.05, description="Contamination factor (Isolation Forest only)."),
    session: SessionState = Depends(get_session)
):
    """
    Detect outliers in all numeric columns using specified method.
    """
    return OutlierService.detect_outliers(session, method, threshold, contamination)

@router.post("/preview", response_model=OutlierPreviewResponse)
async def preview_outlier_treatment(
    request: OutlierRemoveRequest
):
    """
    Preview the effect of outlier removal or capping on the dataset.
    """
    session = get_session(request.session_id)
    return OutlierService.preview_treatment(
        session, 
        request.column, 
        request.method, 
        request.action, 
        request.threshold, 
        request.contamination
    )

@router.post("/remove")
async def apply_outlier_treatment(
    request: OutlierRemoveRequest,
    background_tasks: BackgroundTasks,
    background: bool = Query(False, description="Whether to run outlier removal asynchronously in the background.")
):
    """
    Treat outliers in a numeric column. Supports synchronous or background execution.
    """
    if not background:
        session = get_session(request.session_id)
        OutlierService.apply_treatment(
            session, 
            request.column, 
            request.method, 
            request.action, 
            request.threshold, 
            request.contamination
        )
        return {
            "status": "success",
            "message": f"Outlier treatment '{request.action.value}' successfully applied to column '{request.column}' via '{request.method.value}' method."
        }
    else:
        task = task_service.create_task(request.session_id, "outliers")
        background_tasks.add_task(
            run_background_outlier_treatment, 
            request.session_id, 
            request.column, 
            request.method, 
            request.action, 
            request.threshold, 
            request.contamination,
            task.task_id
        )
        return {
            "task_id": task.task_id,
            "message": "Outlier treatment task started in background."
        }
