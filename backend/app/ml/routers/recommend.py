"""
ML Architect recommendation router.
POST /api/v1/ml/recommend
"""
import logging
from fastapi import APIRouter, HTTPException

from app.ml.schemas.recommendation_schema import RecommendRequest, RecommendResponse, FeedbackRequest
from app.ml.services.recommendation_service import recommend

from app.exceptions.session_exceptions import SessionNotFound
from app.exceptions.validation_exceptions import ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ml",
    tags=["ML Architect"]
)


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="Get ML algorithm recommendations",
    description=(
        "Analyzes the dataset in the given session and recommends the best "
        "ML algorithms using rule filters, SBERT similarity, and LLM reasoning. "
        "Returns ranked recommendations with roles, confidence scores, "
        "a comparison table, and generated sklearn Pipeline code."
    )
)
async def get_recommendations(request: RecommendRequest):
    """
    ML Architect endpoint.

    Input:
        - session_id: Active session with uploaded dataset
        - target_column: (optional) Target variable name
        - problem_type: (optional) classification/regression/clustering/etc.
        - goal: (optional) Natural language description of the ML goal

    Output:
        - dataset_profile: Extracted dataset features
        - recommendations: Primary algorithm recommendation with confidence
        - alternatives: Comparison table of top alternatives
        - suggested_pipeline: Ordered preprocessing steps
        - pipeline_code: Ready-to-run sklearn Pipeline code
        - confidence: Overall confidence score
    """
    try:
        logger.info(f"ML Recommend request: session={request.session_id}")
        response = recommend(request)
        return response
    except (SessionNotFound, ValidationException):
        raise
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}"
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"ML Recommend failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"ML recommendation failed: {str(e)}"
        ) from e


@router.post(
    "/feedback",
    summary="Record user feedback on recommendations",
    description="Logs whether a user accepted or rejected the primary recommended algorithm."
)
async def record_feedback(request: FeedbackRequest):
    """
    Record recommendation feedback.
    """
    try:
        from app.services.supabase_service import SupabaseService
        from app.utils.dataframe_cache import get_session
        
        # Verify session exists
        get_session(request.session_id)
        
        res = SupabaseService.create_recommendation_feedback(
            session_id=request.session_id,
            recommended_algorithm=request.recommended_algorithm,
            accepted=request.accepted,
            user_id=request.user_id
        )
        return {"success": True, "data": res}
    except (SessionNotFound, ValidationException):
        raise
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {request.session_id}"
        ) from e
    except Exception as e:
        logger.error(f"Failed to record feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record feedback: {str(e)}"
        ) from e
