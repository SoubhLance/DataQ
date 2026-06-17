from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None

class ApiErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    detail: str
