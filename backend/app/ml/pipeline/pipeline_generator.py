"""
Template-based sklearn Pipeline code generator.
Generates ready-to-run Python code based on algorithm and preprocessing requirements.
"""
import json
import logging
import os
from typing import List, Optional, Dict, Any

from app.ml.schemas.algorithm_schema import AlgorithmEntry, PreprocessingTemplate
from app.ml.schemas.dataset_profile_schema import DatasetProfile
from app.ml.schemas.recommendation_schema import SuggestedPipelineStep

logger = logging.getLogger(__name__)

# Load preprocessing templates
_TEMPLATES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "kb", "preprocessing_templates.json"
)


def _load_templates() -> Dict[str, PreprocessingTemplate]:
    """Load preprocessing templates from KB."""
    try:
        with open(_TEMPLATES_PATH, "r") as f:
            raw = json.load(f)
        return {k: PreprocessingTemplate(**v) for k, v in raw.items()}
    except Exception as e:
        logger.error(f"Failed to load preprocessing templates: {e}")
        return {}


def get_pipeline_steps(
    algorithm: AlgorithmEntry,
    profile: DatasetProfile
) -> List[SuggestedPipelineStep]:
    """
    Get the ordered list of preprocessing steps for a given algorithm.

    Args:
        algorithm: The recommended algorithm.
        profile: Dataset profile.

    Returns:
        Ordered list of SuggestedPipelineStep objects.
    """
    templates = _load_templates()
    template = templates.get(algorithm.id)

    steps = []

    if template is None:
        # Fallback: basic preprocessing
        logger.warning(f"No template for {algorithm.id}, using defaults.")
        if profile.missing_ratio > 0:
            steps.append(SuggestedPipelineStep(
                step="imputation",
                component="SimpleImputer",
                parameters={"strategy": "median"}
            ))
        if profile.categorical_count > 0:
            steps.append(SuggestedPipelineStep(
                step="encoding",
                component="OneHotEncoder",
                parameters={"handle_unknown": "ignore", "sparse_output": False}
            ))
        steps.append(SuggestedPipelineStep(
            step="scaling",
            component="StandardScaler",
            parameters={}
        ))
        return steps

    # Build steps from template
    if template.imputer:
        if template.imputer == "ffill":
            steps.append(SuggestedPipelineStep(
                step="imputation",
                component="Forward Fill (df.ffill())",
                parameters={"method": "ffill"}
            ))
        else:
            steps.append(SuggestedPipelineStep(
                step="imputation",
                component="SimpleImputer",
                parameters={"strategy": template.imputer}
            ))

    if template.encoding:
        if template.encoding == "onehot":
            steps.append(SuggestedPipelineStep(
                step="encoding",
                component="OneHotEncoder",
                parameters={"handle_unknown": "ignore", "sparse_output": False}
            ))
        elif template.encoding == "label":
            steps.append(SuggestedPipelineStep(
                step="encoding",
                component="LabelEncoder / OrdinalEncoder",
                parameters={"handle_unknown": "use_encoded_value", "unknown_value": -1}
            ))

    if template.scaling:
        if template.scaling == "standard":
            steps.append(SuggestedPipelineStep(
                step="scaling",
                component="StandardScaler",
                parameters={}
            ))
        elif template.scaling == "minmax":
            steps.append(SuggestedPipelineStep(
                step="scaling",
                component="MinMaxScaler",
                parameters={}
            ))

    if template.feature_selection:
        if template.feature_selection == "pca":
            steps.append(SuggestedPipelineStep(
                step="feature_selection",
                component="PCA",
                parameters={"n_components": 0.95}
            ))

    return steps


def generate_pipeline_code(
    algorithm: AlgorithmEntry,
    profile: DatasetProfile,
    steps: List[SuggestedPipelineStep]
) -> str:
    """
    Generate a complete, runnable sklearn Pipeline Python script.

    Args:
        algorithm: The recommended algorithm.
        profile: Dataset profile.
        steps: Preprocessing pipeline steps.

    Returns:
        Python code string.
    """
    # Determine imports
    imports = [
        "import pandas as pd",
        "from sklearn.model_selection import train_test_split",
        "from sklearn.pipeline import Pipeline",
    ]

    pipeline_steps_code = []
    step_imports = set()

    for step in steps:
        if step.component == "SimpleImputer":
            step_imports.add("from sklearn.impute import SimpleImputer")
            strategy = step.parameters.get("strategy", "median")
            pipeline_steps_code.append(
                f'    ("imputer", SimpleImputer(strategy="{strategy}"))'
            )
        elif step.component == "OneHotEncoder":
            step_imports.add("from sklearn.preprocessing import OneHotEncoder")
            step_imports.add("from sklearn.compose import ColumnTransformer")
            # OneHotEncoder will be handled via ColumnTransformer below
        elif step.component == "LabelEncoder / OrdinalEncoder":
            step_imports.add("from sklearn.preprocessing import OrdinalEncoder")
            pipeline_steps_code.append(
                '    ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1))'
            )
        elif step.component == "StandardScaler":
            step_imports.add("from sklearn.preprocessing import StandardScaler")
            pipeline_steps_code.append(
                '    ("scaler", StandardScaler())'
            )
        elif step.component == "MinMaxScaler":
            step_imports.add("from sklearn.preprocessing import MinMaxScaler")
            pipeline_steps_code.append(
                '    ("scaler", MinMaxScaler())'
            )
        elif step.component == "PCA":
            step_imports.add("from sklearn.decomposition import PCA")
            n_components = step.parameters.get("n_components", 0.95)
            pipeline_steps_code.append(
                f'    ("pca", PCA(n_components={n_components}))'
            )

    # Add model import and step
    model_import, model_instantiation = _get_model_code(algorithm)
    if model_import:
        step_imports.add(model_import)
    pipeline_steps_code.append(f'    ("model", {model_instantiation})')

    # Determine metrics
    if profile.problem_type == "classification":
        step_imports.add("from sklearn.metrics import accuracy_score, classification_report")
        metric_code = _classification_metric_code()
    elif profile.problem_type == "regression":
        step_imports.add("from sklearn.metrics import mean_squared_error, r2_score")
        metric_code = _regression_metric_code()
    else:
        metric_code = '# Evaluate results as needed for this task type\nprint("Model fitted successfully.")'

    # Combine imports
    all_imports = imports + sorted(step_imports)

    # Build the final script
    target_col = profile.target_column or "target"
    has_onehot = any(s.component == "OneHotEncoder" for s in steps)

    if has_onehot and profile.categorical_columns:
        return _generate_column_transformer_script(
            all_imports, pipeline_steps_code, metric_code,
            profile, algorithm, target_col
        )
    else:
        return _generate_simple_pipeline_script(
            all_imports, pipeline_steps_code, metric_code,
            target_col
        )


def _generate_simple_pipeline_script(
    imports: list,
    pipeline_steps: list,
    metric_code: str,
    target_col: str
) -> str:
    """Generate a simple Pipeline script."""
    imports_str = "\n".join(imports)
    steps_str = ",\n".join(pipeline_steps)

    return f'''{imports_str}

# Load your dataset
df = pd.read_csv("your_dataset.csv")

# Separate features and target
X = df.drop(columns=["{target_col}"])
y = df["{target_col}"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build pipeline
pipeline = Pipeline([
{steps_str}
])

# Train
pipeline.fit(X_train, y_train)

# Predict
y_pred = pipeline.predict(X_test)

# Evaluate
{metric_code}
'''


def _generate_column_transformer_script(
    imports: list,
    pipeline_steps: list,
    metric_code: str,
    profile: DatasetProfile,
    algorithm: AlgorithmEntry,
    target_col: str
) -> str:
    """Generate a ColumnTransformer-based Pipeline script for mixed types."""
    imports_str = "\n".join(imports)
    model_import, model_inst = _get_model_code(algorithm)

    num_cols = [c for c in profile.numeric_columns if c != target_col]
    cat_cols = [c for c in profile.categorical_columns if c != target_col]

    # Build sub-pipeline steps for numeric
    num_steps = []
    has_imputer = any("imputer" in s for s in pipeline_steps)
    has_scaler = any("scaler" in s for s in pipeline_steps)

    if has_imputer:
        num_steps.append('("imputer", SimpleImputer(strategy="median"))')
    if has_scaler:
        if any("StandardScaler" in s for s in pipeline_steps):
            num_steps.append('("scaler", StandardScaler())')
        elif any("MinMaxScaler" in s for s in pipeline_steps):
            num_steps.append('("scaler", MinMaxScaler())')

    num_pipeline_str = ", ".join(num_steps) if num_steps else '("passthrough", "passthrough")'
    cat_pipeline_str = '("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))'

    return f'''{imports_str}

# Load your dataset
df = pd.read_csv("your_dataset.csv")

# Separate features and target
X = df.drop(columns=["{target_col}"])
y = df["{target_col}"]

# Define column groups
numeric_features = {num_cols}
categorical_features = {cat_cols}

# Build preprocessor
preprocessor = ColumnTransformer(
    transformers=[
        ("num", Pipeline([{num_pipeline_str}]), numeric_features),
        ("cat", Pipeline([{cat_pipeline_str}]), categorical_features),
    ],
    remainder="drop"
)

# Build full pipeline
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", {model_inst})
])

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train
pipeline.fit(X_train, y_train)

# Predict
y_pred = pipeline.predict(X_test)

# Evaluate
{metric_code}
'''


def _get_model_code(algorithm: AlgorithmEntry) -> tuple:
    """Get the import statement and instantiation code for a model."""
    sklearn_class = algorithm.sklearn_class

    # Handle common cases
    _MODEL_MAP = {
        "sklearn.linear_model.LogisticRegression": ("from sklearn.linear_model import LogisticRegression", "LogisticRegression(max_iter=1000)"),
        "sklearn.tree.DecisionTreeClassifier": ("from sklearn.tree import DecisionTreeClassifier", "DecisionTreeClassifier(random_state=42)"),
        "sklearn.ensemble.RandomForestClassifier": ("from sklearn.ensemble import RandomForestClassifier", "RandomForestClassifier(n_estimators=100, random_state=42)"),
        "sklearn.ensemble.ExtraTreesClassifier": ("from sklearn.ensemble import ExtraTreesClassifier", "ExtraTreesClassifier(n_estimators=100, random_state=42)"),
        "xgboost.XGBClassifier": ("from xgboost import XGBClassifier", "XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')"),
        "lightgbm.LGBMClassifier": ("from lightgbm import LGBMClassifier", "LGBMClassifier(n_estimators=100, random_state=42, verbose=-1)"),
        "catboost.CatBoostClassifier": ("from catboost import CatBoostClassifier", "CatBoostClassifier(iterations=100, random_state=42, verbose=0)"),
        "sklearn.svm.SVC": ("from sklearn.svm import SVC", "SVC(kernel='rbf', random_state=42)"),
        "sklearn.neighbors.KNeighborsClassifier": ("from sklearn.neighbors import KNeighborsClassifier", "KNeighborsClassifier(n_neighbors=5)"),
        "sklearn.naive_bayes.GaussianNB": ("from sklearn.naive_bayes import GaussianNB", "GaussianNB()"),
        "sklearn.neural_network.MLPClassifier": ("from sklearn.neural_network import MLPClassifier", "MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)"),
        "sklearn.ensemble.AdaBoostClassifier": ("from sklearn.ensemble import AdaBoostClassifier", "AdaBoostClassifier(n_estimators=100, random_state=42)"),
        "sklearn.ensemble.GradientBoostingClassifier": ("from sklearn.ensemble import GradientBoostingClassifier", "GradientBoostingClassifier(n_estimators=100, random_state=42)"),
        "sklearn.linear_model.LinearRegression": ("from sklearn.linear_model import LinearRegression", "LinearRegression()"),
        "sklearn.linear_model.Ridge": ("from sklearn.linear_model import Ridge", "Ridge(alpha=1.0)"),
        "sklearn.linear_model.Lasso": ("from sklearn.linear_model import Lasso", "Lasso(alpha=1.0)"),
        "sklearn.linear_model.ElasticNet": ("from sklearn.linear_model import ElasticNet", "ElasticNet(alpha=1.0, l1_ratio=0.5)"),
        "sklearn.ensemble.RandomForestRegressor": ("from sklearn.ensemble import RandomForestRegressor", "RandomForestRegressor(n_estimators=100, random_state=42)"),
        "xgboost.XGBRegressor": ("from xgboost import XGBRegressor", "XGBRegressor(n_estimators=100, random_state=42)"),
        "lightgbm.LGBMRegressor": ("from lightgbm import LGBMRegressor", "LGBMRegressor(n_estimators=100, random_state=42, verbose=-1)"),
        "catboost.CatBoostRegressor": ("from catboost import CatBoostRegressor", "CatBoostRegressor(iterations=100, random_state=42, verbose=0)"),
        "sklearn.svm.SVR": ("from sklearn.svm import SVR", "SVR(kernel='rbf')"),
        "sklearn.tree.DecisionTreeRegressor": ("from sklearn.tree import DecisionTreeRegressor", "DecisionTreeRegressor(random_state=42)"),
        "sklearn.ensemble.GradientBoostingRegressor": ("from sklearn.ensemble import GradientBoostingRegressor", "GradientBoostingRegressor(n_estimators=100, random_state=42)"),
        "sklearn.cluster.KMeans": ("from sklearn.cluster import KMeans", "KMeans(n_clusters=3, random_state=42)"),
        "sklearn.cluster.DBSCAN": ("from sklearn.cluster import DBSCAN", "DBSCAN(eps=0.5, min_samples=5)"),
        "sklearn.cluster.AgglomerativeClustering": ("from sklearn.cluster import AgglomerativeClustering", "AgglomerativeClustering(n_clusters=3)"),
        "sklearn.mixture.GaussianMixture": ("from sklearn.mixture import GaussianMixture", "GaussianMixture(n_components=3, random_state=42)"),
        "sklearn.decomposition.PCA": ("from sklearn.decomposition import PCA", "PCA(n_components=2)"),
        "sklearn.manifold.TSNE": ("from sklearn.manifold import TSNE", "TSNE(n_components=2, random_state=42)"),
    }

    if sklearn_class in _MODEL_MAP:
        return _MODEL_MAP[sklearn_class]

    # Fallback: try to parse the class path
    parts = sklearn_class.rsplit(".", 1)
    if len(parts) == 2:
        return (f"from {parts[0]} import {parts[1]}", f"{parts[1]}()")

    return ("", f"# {sklearn_class}()")


def _classification_metric_code() -> str:
    return '''print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\\nClassification Report:")
print(classification_report(y_test, y_pred))'''


def _regression_metric_code() -> str:
    return '''print(f"R² Score: {r2_score(y_test, y_pred):.4f}")
print(f"RMSE: {mean_squared_error(y_test, y_pred, squared=False):.4f}")'''
