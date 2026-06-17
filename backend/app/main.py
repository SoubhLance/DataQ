import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.utils.cache_cleanup import start_cache_cleanup_service, stop_cache_cleanup_service

# Import exceptions
from app.exceptions.session_exceptions import SessionException, SessionNotFound, SessionExpired
from app.exceptions.validation_exceptions import ValidationException, UnsupportedFileType, FileTooLarge
from app.exceptions.dataset_exceptions import DatasetException, ColumnNotFound, InvalidDtype, EmptyDataset, OperationError

# Import routers
from app.routers import (
    upload, inspect, duplicates, missing_values, 
    outliers, columns, scaling, export, visualization,
    agent, task
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start session cache cleanup background worker
    logger.info("Initializing application startup sequence...")
    start_cache_cleanup_service(interval_seconds=60)
    yield
    # Shutdown: Stop session cache cleanup background worker
    logger.info("Initializing application shutdown sequence...")
    stop_cache_cleanup_service()

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Global Exception Handlers ---

@app.exception_handler(SessionNotFound)
async def session_not_found_handler(request: Request, exc: SessionNotFound):
    logger.warning(f"Session error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "SESSION_NOT_FOUND", "message": str(exc)}
    )

@app.exception_handler(SessionExpired)
async def session_expired_handler(request: Request, exc: SessionExpired):
    logger.warning(f"Session expired: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={"detail": "SESSION_EXPIRED", "message": str(exc)}
    )

@app.exception_handler(UnsupportedFileType)
async def unsupported_file_type_handler(request: Request, exc: UnsupportedFileType):
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "UNSUPPORTED_FILE_TYPE", "message": str(exc), "allowed": exc.allowed}
    )

@app.exception_handler(FileTooLarge)
async def file_too_large_handler(request: Request, exc: FileTooLarge):
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"detail": "FILE_TOO_LARGE", "message": str(exc), "limit_bytes": exc.limit}
    )

@app.exception_handler(ColumnNotFound)
async def column_not_found_handler(request: Request, exc: ColumnNotFound):
    logger.warning(f"Dataset error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "COLUMN_NOT_FOUND", "message": str(exc)}
    )

@app.exception_handler(InvalidDtype)
async def invalid_dtype_handler(request: Request, exc: InvalidDtype):
    logger.warning(f"Dataset error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "INVALID_DATATYPE_CAST", "message": str(exc)}
    )

@app.exception_handler(EmptyDataset)
async def empty_dataset_handler(request: Request, exc: EmptyDataset):
    logger.error(f"Dataset error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "EMPTY_DATASET", "message": str(exc)}
    )

@app.exception_handler(OperationError)
async def operation_error_handler(request: Request, exc: OperationError):
    logger.error(f"Processing error during {exc.operation}: {exc.details}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": f"OPERATION_FAILED_{exc.operation.upper()}", "message": str(exc)}
    )

@app.exception_handler(ValidationException)
async def base_validation_handler(request: Request, exc: ValidationException):
    logger.warning(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "VALIDATION_FAILED", "message": str(exc)}
    )

# --- Register Routers ---
app.include_router(upload.router, prefix=settings.API_V1_STR)
app.include_router(inspect.router, prefix=settings.API_V1_STR)
app.include_router(duplicates.router, prefix=settings.API_V1_STR)
app.include_router(missing_values.router, prefix=settings.API_V1_STR)
app.include_router(outliers.router, prefix=settings.API_V1_STR)
app.include_router(columns.router, prefix=settings.API_V1_STR)
app.include_router(scaling.router, prefix=settings.API_V1_STR)
app.include_router(export.router, prefix=settings.API_V1_STR)
app.include_router(visualization.router, prefix=settings.API_V1_STR)
app.include_router(agent.router, prefix=settings.API_V1_STR)
app.include_router(task.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs_url": "/docs"
    }
