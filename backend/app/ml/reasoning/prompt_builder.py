"""
Builds structured LLM prompts from dataset profile and ranked algorithms.
"""
import logging
from typing import List

from app.ml.schemas.algorithm_schema import AlgorithmEntry
from app.ml.schemas.dataset_profile_schema import DatasetProfile

logger = logging.getLogger(__name__)


def build_recommendation_prompt(
    profile: DatasetProfile,
    ranked_algorithms: List[AlgorithmEntry]
) -> str:
    """
    Build a structured prompt for the LLM to assign roles to algorithms.

    The LLM must respond with a JSON object assigning roles:
    - recommended: best overall choice
    - fastest: fastest training/prediction
    - best_accuracy_boost: highest accuracy potential
    - most_interpretable: most interpretable model

    Args:
        profile: Dataset profile.
        ranked_algorithms: Top-N ranked algorithms with scores.

    Returns:
        Formatted prompt string.
    """
    # Build algorithm section
    algo_lines = []
    for i, algo in enumerate(ranked_algorithms, 1):
        algo_lines.append(
            f"{i}. {algo.name} (id={algo.id})\n"
            f"   - Category: {algo.category}\n"
            f"   - Speed: {algo.speed}\n"
            f"   - Accuracy Potential: {algo.accuracy_potential}\n"
            f"   - Interpretability: {algo.interpretability}\n"
            f"   - Similarity Score: {algo.similarity_score:.3f}\n"
            f"   - Handles Imbalance: {algo.handles_imbalance}\n"
            f"   - Handles Categorical: {algo.handles_categorical}\n"
            f"   - Strengths: {', '.join(algo.strengths)}\n"
            f"   - Weaknesses: {', '.join(algo.weaknesses)}"
        )

    algorithms_text = "\n".join(algo_lines)

    # Dataset summary
    balance_text = ""
    if profile.class_balance is not None:
        balance_text = f"- Class Balance (minority/majority): {profile.class_balance}\n"

    prompt = f"""You are an ML Architect analyzing a dataset to recommend the best machine learning algorithms.

## Dataset Profile
- Rows: {profile.row_count}
- Columns: {profile.column_count}
- Problem Type: {profile.problem_type}
- Target Column: {profile.target_column or 'Not specified'}
- Numeric Ratio: {profile.numeric_ratio:.0%}
- Categorical Ratio: {profile.categorical_ratio:.0%}
- Missing Ratio: {profile.missing_ratio:.0%}
- Outlier Ratio: {profile.outlier_ratio:.0%}
- Dimensionality Ratio: {profile.dimensionality_ratio:.4f}
{balance_text}- High Cardinality Columns: {', '.join(profile.high_cardinality_columns) if profile.high_cardinality_columns else 'None'}

## Feature Description
{profile.feature_description}

## Candidate Algorithms (ranked by similarity)
{algorithms_text}

## Your Task
Assign exactly ONE role to each of the top 4 algorithms from the candidates above:

1. **recommended** — The best overall algorithm for this specific dataset
2. **fastest** — The fastest to train and predict
3. **best_accuracy_boost** — The one likely to achieve the highest accuracy
4. **most_interpretable** — The most interpretable/explainable model

For each assignment, provide a 1-2 sentence reasoning explaining WHY this algorithm fits this role for THIS specific dataset.

## Required Output Format
Respond with ONLY a valid JSON object, no markdown, no explanation outside JSON:

{{
  "assignments": [
    {{
      "id": "<algorithm_id>",
      "role": "recommended",
      "reasoning": "<1-2 sentence reasoning>"
    }},
    {{
      "id": "<algorithm_id>",
      "role": "fastest",
      "reasoning": "<1-2 sentence reasoning>"
    }},
    {{
      "id": "<algorithm_id>",
      "role": "best_accuracy_boost",
      "reasoning": "<1-2 sentence reasoning>"
    }},
    {{
      "id": "<algorithm_id>",
      "role": "most_interpretable",
      "reasoning": "<1-2 sentence reasoning>"
    }}
  ]
}}

IMPORTANT:
- Each role must be assigned to a different algorithm.
- Only use algorithm IDs from the candidate list.
- If fewer than 4 candidates exist, assign available roles only.
"""

    return prompt


def build_system_instruction() -> str:
    """Build the system instruction for the ML Architect LLM call."""
    return (
        "You are an expert ML Architect. You analyze datasets and recommend "
        "the most appropriate machine learning algorithms. You always respond "
        "with valid JSON only. You are precise, data-driven, and consider "
        "dataset characteristics when making recommendations."
    )
