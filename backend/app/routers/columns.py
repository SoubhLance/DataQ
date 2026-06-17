from fastapi import APIRouter, Depends
from typing import List
from app.utils.dataframe_cache import get_session
from app.models.session_model import SessionState
from app.schemas.column_schema import (
    ColumnDropRequest, ColumnRenameRequest, ColumnCastRequest, 
    ColumnEncodeRequest, ColumnEncodePreviewResponse
)
from app.services.column_service import ColumnService

router = APIRouter(prefix="/columns", tags=["Column Operations"])

@router.get("/{session_id}", response_model=List[str])
async def get_columns(session: SessionState = Depends(get_session)):
    """
    Get a list of all column names in the dataset.
    """
    return ColumnService.get_columns(session)

@router.post("/drop")
async def drop_columns(
    request: ColumnDropRequest
):
    """
    Drop one or more columns from the dataset.
    """
    session = get_session(request.session_id)
    ColumnService.drop_columns(session, request.columns)
    return {
        "status": "success",
        "message": f"Successfully dropped columns: {request.columns}."
    }

@router.post("/rename")
async def rename_column(
    request: ColumnRenameRequest
):
    """
    Rename a column in the dataset.
    """
    session = get_session(request.session_id)
    ColumnService.rename_column(session, request.old_name, request.new_name)
    return {
        "status": "success",
        "message": f"Column '{request.old_name}' successfully renamed to '{request.new_name}'."
    }

@router.post("/change_dtype")
async def change_column_dtype(
    request: ColumnCastRequest
):
    """
    Cast column to target data type: 'int', 'float', 'string', 'datetime'.
    """
    session = get_session(request.session_id)
    ColumnService.change_dtype(session, request.column, request.new_dtype)
    return {
        "status": "success",
        "message": f"Column '{request.column}' successfully casted to type '{request.new_dtype.value}'."
    }

@router.post("/encode/preview", response_model=ColumnEncodePreviewResponse)
async def preview_column_encoding(
    request: ColumnEncodeRequest
):
    """
    Preview the effect of label encoding or one-hot encoding on the column values.
    """
    session = get_session(request.session_id)
    return ColumnService.preview_encoding(session, request.column, request.method)

@router.post("/encode")
async def encode_column(
    request: ColumnEncodeRequest
):
    """
    Encode a categorical column (Label or One-Hot) and register the action in pipeline history.
    """
    session = get_session(request.session_id)
    ColumnService.apply_encoding(session, request.column, request.method)
    return {
        "status": "success",
        "message": f"Column '{request.column}' successfully encoded using '{request.method.value}' encoding."
    }
