"""
LLM Reasoner that calls the existing ai_service for role assignment.
Falls back to rule-based assignment if LLM fails.
"""
import json
import logging
import re
from typing import List, Dict, Optional

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile
from app.ml.reasoning.prompt_builder import build_recommendation_prompt, build_system_instruction

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response text."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown code fences
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object
    json_match = re.search(r'\{[^{}]*"assignments"[^{}]*\[.*?\]\s*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _rule_based_assignment(algorithms: List[AlgorithmEntry]) -> List[Dict]:
    """
    Fallback: assign roles based on algorithm metadata when LLM is unavailable.
    """
    if not algorithms:
        return []

    assignments = []
    used_ids = set()

    # Sort for role assignment
    # 1. Recommended = highest combined_score
    by_combined = sorted(algorithms, key=lambda a: a.combined_score, reverse=True)
    for algo in by_combined:
        if algo.id not in used_ids:
            assignments.append({
                "id": algo.id,
                "role": "recommended",
                "reasoning": f"{algo.name} has the highest combined score ({algo.combined_score:.3f}) based on dataset similarity and filter analysis."
            })
            used_ids.add(algo.id)
            break

    # 2. Fastest = speed == "fast" with highest score
    speed_order = {"fast": 3, "medium": 2, "slow": 1}
    by_speed = sorted(
        algorithms,
        key=lambda a: (speed_order.get(a.speed, 0), a.combined_score),
        reverse=True
    )
    for algo in by_speed:
        if algo.id not in used_ids:
            assignments.append({
                "id": algo.id,
                "role": "fastest",
                "reasoning": f"{algo.name} offers {algo.speed} training speed, ideal for rapid iteration."
            })
            used_ids.add(algo.id)
            break

    # 3. Best accuracy boost = accuracy_potential == "very_high" or "high"
    acc_order = {"very_high": 4, "high": 3, "medium": 2}
    by_accuracy = sorted(
        algorithms,
        key=lambda a: (acc_order.get(a.accuracy_potential, 0), a.combined_score),
        reverse=True
    )
    for algo in by_accuracy:
        if algo.id not in used_ids:
            assignments.append({
                "id": algo.id,
                "role": "best_accuracy_boost",
                "reasoning": f"{algo.name} has {algo.accuracy_potential} accuracy potential for this dataset."
            })
            used_ids.add(algo.id)
            break

    # 4. Most interpretable = interpretability == "high"
    interp_order = {"high": 3, "medium": 2, "low": 1}
    by_interp = sorted(
        algorithms,
        key=lambda a: (interp_order.get(a.interpretability, 0), a.combined_score),
        reverse=True
    )
    for algo in by_interp:
        if algo.id not in used_ids:
            assignments.append({
                "id": algo.id,
                "role": "most_interpretable",
                "reasoning": f"{algo.name} provides {algo.interpretability} interpretability with explainable outputs."
            })
            used_ids.add(algo.id)
            break

    return assignments


def reason_with_llm(
    profile: DatasetProfile,
    ranked_algorithms: List[AlgorithmEntry]
) -> List[Dict]:
    """
    Use the AI fallback chain to assign roles to algorithms.
    Falls back to rule-based assignment if LLM fails.

    Args:
        profile: Dataset profile.
        ranked_algorithms: Top-N ranked algorithms.

    Returns:
        List of assignment dicts with id, role, reasoning.
    """
    if not ranked_algorithms:
        return []

    # Build the prompt
    prompt = build_recommendation_prompt(profile, ranked_algorithms)
    system_instruction = build_system_instruction()

    try:
        from app.services.ai_service import ai_service
        logger.info("Calling AI service for role assignment...")
        response = ai_service.generate(prompt, system_instruction)

        # Parse the JSON response
        parsed = _extract_json(response)
        if parsed and "assignments" in parsed:
            assignments = parsed["assignments"]
            # Validate assignments
            valid_ids = {algo.id for algo in ranked_algorithms}
            valid_roles = {"recommended", "fastest", "best_accuracy_boost", "most_interpretable"}

            validated = []
            seen_roles = set()
            for assignment in assignments:
                aid = assignment.get("id", "")
                role = assignment.get("role", "")
                if aid in valid_ids and role in valid_roles and role not in seen_roles:
                    validated.append(assignment)
                    seen_roles.add(role)

            if validated:
                logger.info(f"LLM assigned {len(validated)} roles successfully.")
                return validated
            else:
                logger.warning("LLM returned invalid assignments, falling back to rule-based.")
        else:
            logger.warning("LLM response could not be parsed as JSON, falling back to rule-based.")

    except Exception as e:
        logger.warning(f"LLM reasoning failed: {e}. Falling back to rule-based assignment.")

    # Fallback to rule-based
    logger.info("Using rule-based role assignment.")
    return _rule_based_assignment(ranked_algorithms)
