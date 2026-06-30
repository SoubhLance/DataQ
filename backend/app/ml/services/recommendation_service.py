"""
ML Recommendation Orchestrator Service.
Coordinates: Profile -> Filter -> Rank -> Reason -> Generate Pipeline.
"""
import json
import logging
import os
from typing import List, Optional, Dict

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile
from app.ml.schemas.recommendation_schema import (
    RecommendRequest,
    RecommendResponse,
    AlgorithmRecommendation,
    AlternativeComparison,
    SuggestedPipelineStep,
)

from app.ml.profiling.dataset_profiler import profile_dataset
from app.ml.filters.problem_type_filter import filter_by_problem_type
from app.ml.filters.dataset_size_filter import filter_by_dataset_size
from app.ml.filters.imbalance_filter import filter_by_imbalance
from app.ml.filters.dimensionality_filter import filter_by_dimensionality
from app.ml.filters.categorical_support_filter import filter_by_categorical_support
from app.ml.ranking.sbert_ranker import rank_algorithms
from app.ml.reasoning.llm_reasoner import reason_with_llm
from app.ml.pipeline.pipeline_generator import generate_pipeline_code, get_pipeline_steps

logger = logging.getLogger(__name__)

# Path to KB file
_KB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kb", "ml_algorithm_kb.json")


def _load_kb() -> List[AlgorithmEntry]:
    """Load all algorithms from the knowledge base."""
    kb_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "kb", "ml_algorithm_kb.json"
    )
    try:
        with open(kb_path, "r") as f:
            raw = json.load(f)
        algorithms = [AlgorithmEntry(**entry) for entry in raw]
        logger.info(f"Loaded {len(algorithms)} algorithms from KB.")
        return algorithms
    except Exception as e:
        logger.error(f"Failed to load algorithm KB: {e}")
        raise RuntimeError(f"Failed to load algorithm KB: {e}") from e


def _build_alternatives_table(
    ranked: List[AlgorithmEntry],
    role_map: Dict[str, str]
) -> List[AlternativeComparison]:
    """Build the comparison alternatives table."""
    alternatives = []
    for algo in ranked:
        role = role_map.get(algo.id, "candidate")
        alternatives.append(AlternativeComparison(
            algorithm=algo.name,
            role=role,
            speed=algo.speed.capitalize(),
            accuracy=algo.accuracy_potential.replace("_", " ").capitalize(),
            interpretability=algo.interpretability.capitalize(),
            handles_categorical=algo.handles_categorical,
            handles_imbalance=algo.handles_imbalance,
            confidence=round(algo.combined_score, 4)
        ))
    return alternatives


def _build_recommendation(
    algo: AlgorithmEntry,
    role: str,
    reasoning: str
) -> AlgorithmRecommendation:
    """Build a single AlgorithmRecommendation from an AlgorithmEntry."""
    return AlgorithmRecommendation(
        id=algo.id,
        name=algo.name,
        category=algo.category,
        role=role,
        confidence=round(algo.combined_score, 4),
        similarity_score=round(algo.similarity_score, 4),
        reasoning=reasoning,
        strengths=algo.strengths,
        weaknesses=algo.weaknesses,
        explainability=algo.explainability.model_dump()
    )


def recommend(request: RecommendRequest) -> RecommendResponse:
    """
    Main recommendation entry point.

    Flow:
    1. Load session → get DataFrame
    2. Profile dataset
    3. Load KB algorithms
    4. Apply hard filters (problem_type → size → imbalance → dimensionality → categorical)
    5. SBERT rank remaining algorithms
    6. LLM reasoning for role assignment
    7. Generate pipeline code for primary recommendation
    8. Return RecommendResponse

    Args:
        request: RecommendRequest with session_id, target_column, problem_type, goal.

    Returns:
        RecommendResponse with recommendations, alternatives, pipeline code, confidence.
    """
    # 1. Load session
    from app.utils.dataframe_cache import get_session
    session = get_session(request.session_id)
    df = session.current_df

    logger.info(f"ML Recommend: session={request.session_id}, shape={df.shape}")

    # 2. Profile dataset
    profile = profile_dataset(
        df=df,
        session_id=request.session_id,
        target_column=request.target_column,
        problem_type=request.problem_type,
        goal=request.goal
    )

    # 3. Load KB
    all_algorithms = _load_kb()

    # 4. Apply filter chain
    # Reset filter scores
    for algo in all_algorithms:
        algo.filter_score = 0.0

    filtered = filter_by_problem_type(all_algorithms, profile)
    filtered = filter_by_dataset_size(filtered, profile)
    filtered = filter_by_imbalance(filtered, profile)
    filtered = filter_by_dimensionality(filtered, profile)
    filtered = filter_by_categorical_support(filtered, profile)

    if not filtered:
        raise RuntimeError(
            f"No algorithms remaining after filtering for problem_type={profile.problem_type}. "
            f"Dataset may be too small or too specialized."
        )

    logger.info(f"After all filters: {len(filtered)} algorithms remain.")

    # 5. SBERT rank
    top_n = min(8, len(filtered))
    ranked = rank_algorithms(filtered, profile.feature_description, top_n=top_n)

    # 6. LLM reasoning
    assignments = reason_with_llm(profile, ranked)

    # Build role map and reasoning map
    role_map: Dict[str, str] = {}
    reasoning_map: Dict[str, str] = {}
    for assignment in assignments:
        role_map[assignment["id"]] = assignment["role"]
        reasoning_map[assignment["id"]] = assignment.get("reasoning", "")

    # 7. Build recommendations
    all_recommendations = []
    primary_recommendation = None

    for algo in ranked:
        role = role_map.get(algo.id, "candidate")
        reasoning = reasoning_map.get(algo.id, "")
        rec = _build_recommendation(algo, role, reasoning)
        all_recommendations.append(rec)

        if role == "recommended" and primary_recommendation is None:
            primary_recommendation = rec

    # If no "recommended" role assigned, use the top-ranked
    if primary_recommendation is None and all_recommendations:
        primary_recommendation = all_recommendations[0]
        primary_recommendation.role = "recommended"

    # 8. Build alternatives table
    alternatives = _build_alternatives_table(ranked, role_map)

    # 9. Generate pipeline
    primary_algo = None
    for algo in ranked:
        if algo.id == primary_recommendation.id:
            primary_algo = algo
            break

    pipeline_steps = []
    pipeline_code = ""
    if primary_algo:
        pipeline_steps = get_pipeline_steps(primary_algo, profile)
        pipeline_code = generate_pipeline_code(primary_algo, profile, pipeline_steps)

    # 10. Compute confidence scores
    pipeline_conf = primary_recommendation.confidence
    preproc_conf = round(0.95 - (profile.missing_ratio * 0.1) - (profile.outlier_ratio * 0.05), 2)
    preproc_conf = max(0.0, min(1.0, preproc_conf))

    # 11. Persist recommendation to Supabase database (non-blocking)
    recs_data = [r.model_dump() for r in all_recommendations]
    try:
        from app.services.supabase_service import SupabaseService
        SupabaseService.create_ml_recommendation(
            session_id=request.session_id,
            goal=request.goal,
            top_algorithm=primary_recommendation.id,
            confidence=pipeline_conf,
            recommendations=recs_data,
            user_id=None
        )
        logger.info(f"Successfully stored ML recommendation for session {request.session_id} in Supabase.")
    except Exception as db_err:
        logger.warning(f"Could not store ML recommendation in Supabase (non-blocking): {db_err}")

    # 12. Build response
    response = RecommendResponse(
        session_id=request.session_id,
        problem_type=profile.problem_type or "unknown",
        dataset_profile=profile,
        recommendations=primary_recommendation,
        alternatives=alternatives,
        suggested_pipeline=pipeline_steps,
        pipeline_code=pipeline_code,
        confidence=pipeline_conf,
        pipeline_confidence=pipeline_conf,
        preprocessing_confidence=preproc_conf,
        all_recommendations=all_recommendations
    )

    logger.info(
        f"ML Recommendation complete: primary={primary_recommendation.name} "
        f"(confidence={primary_recommendation.confidence})"
    )

    return response
