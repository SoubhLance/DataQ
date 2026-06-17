import os
from enum import Enum
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.services.export_service import ExportService
from app.services.report_service import ReportService
from app.services.pipeline_service import PipelineService
from app.services.task_service import task_service

router = APIRouter(tags=["Export & Operations"])

class PipelineFormat(str, Enum):
    PANDAS = "pandas"
    SKLEARN = "sklearn"
    NOTEBOOK = "notebook"
    YAML = "yaml"

class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    PARQUET = "parquet"

@router.post("/export/file/{session_id}")
async def export_cleaned_file(
    session_id: str,
    format: ExportFormat = Query(ExportFormat.CSV, description="Target file format for export."),
    session: SessionState = Depends(get_session)
):
    """
    Download the cleaned version of the dataset in CSV, XLSX, JSON, or Parquet format.
    """
    filepath = ExportService.export_dataset(session, format.value)
    
    media_types = {
        ExportFormat.CSV: "text/csv",
        ExportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ExportFormat.JSON: "application/json",
        ExportFormat.PARQUET: "application/octet-stream"
    }
    
    filename = f"cleaned_{os.path.splitext(session.filename)[0]}.{format.value}"
    
    return FileResponse(
        filepath, 
        filename=filename, 
        media_type=media_types.get(format, "application/octet-stream")
    )

# Keeping specific endpoint support as requested by USER
@router.post("/export/csv")
async def export_csv_post(
    session_id: str = Query(..., description="Active session UUID."),
    session: SessionState = Depends(get_session)
):
    """
    Standard endpoint to download the cleaned CSV.
    """
    # Force retrieve session matching request query parameter
    session = get_session(session_id)
    filepath = ExportService.export_dataset(session, "csv")
    return FileResponse(
        filepath, 
        filename=f"cleaned_{session.filename}", 
        media_type="text/csv"
    )

def run_background_report_generation(session_id: str, task_id: str):
    try:
        session = get_session(session_id)
        task_service.update_task_progress(task_id, 30, "Compiling summary statistics...")
        task_service.update_task_progress(task_id, 70, "Evaluating outliers and missingness...")
        report = ReportService.generate_json_report(session)
        task_service.complete_task(task_id, result=report)
    except Exception as e:
        task_service.fail_task(task_id, str(e))

@router.post("/export/json-report")
async def generate_json_report(
    background_tasks: BackgroundTasks,
    session_id: str = Query(..., description="Active session UUID."),
    background: bool = Query(False, description="Whether to run the report generation in the background."),
    session: SessionState = Depends(get_session)
):
    """
    Generate the dataset quality check metadata report. Supports sync/async modes.
    """
    if not background:
        session = get_session(session_id)
        return ReportService.generate_json_report(session)
    else:
        task = task_service.create_task(session_id, "report")
        background_tasks.add_task(run_background_report_generation, session_id, task.task_id)
        return {
            "task_id": task.task_id,
            "message": "Report generation started in background."
        }

@router.get("/pipeline/{session_id}")
async def get_pipeline_code(
    session_id: str,
    format: PipelineFormat = Query(PipelineFormat.PANDAS, description="Pipeline formatting structure: pandas, sklearn, notebook, yaml"),
    session: SessionState = Depends(get_session)
):
    """
    Get the Python/YAML cleaning pipeline script containing all transformations applied so far.
    """
    if format == PipelineFormat.PANDAS:
        code = PipelineService.get_pandas_script(session)
        content_type = "text/plain"
    elif format == PipelineFormat.SKLEARN:
        code = PipelineService.get_sklearn_pipeline(session)
        content_type = "text/plain"
    elif format == PipelineFormat.NOTEBOOK:
        code = PipelineService.get_jupyter_notebook(session)
        content_type = "application/json"
    else: # YAML
        code = PipelineService.get_yaml_recipe(session)
        content_type = "text/yaml"
        
    return {
        "format": format.value,
        "content_type": content_type,
        "pipeline": code
    }

@router.post("/undo/{session_id}")
async def undo_last_step(
    session_id: str,
    session: SessionState = Depends(get_session)
):
    """
    Rollback the last applied preprocessing operation.
    """
    PipelineService.undo_last_operation(session)
    return {
        "status": "success",
        "message": "Last operation successfully reverted.",
        "operations_remaining": len(session.operations),
        "rows": session.rows,
        "columns": session.columns
    }

@router.get("/operations/{session_id}")
async def get_operations_history(
    session: SessionState = Depends(get_session)
):
    """
    Get the ordered log of preprocessing operations applied to the dataset in this session.
    """
    return [
        {
            "type": op.type,
            "time": op.created_at.isoformat(),
            "description": op.description,
            "params": op.params
        }
        for op in session.operations
    ]
