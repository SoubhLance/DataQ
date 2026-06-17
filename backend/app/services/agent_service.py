import logging
import pandas as pd
from app.models.session_model import SessionState
from app.core.profiler import DatasetProfiler
from app.services.statistics_service import StatisticsService
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

class AgentService:
    """
    Simulates a production-grade AI dataset analyst assistant.
    Analyzes the dataset properties to provide intelligent answers to user queries,
    assisting in model suggestions, data cleaning, and dataset diagnostics.
    """
    @staticmethod
    def process_chat_message(session: SessionState, message: str) -> str:
        """
        Processes a chat message, analyzing the current dataset in context
        and returns a custom analytical response.
        """
        df = session.current_df
        profiler = DatasetProfiler(df)
        msg_lower = message.lower()
        
        # 1. Base Metadata
        num_cols = len(profiler.numeric_columns)
        cat_cols = len(profiler.categorical_columns)
        total_rows = len(df)
        total_cols = len(df.columns)
        
        # Get quality metrics
        quality = StatisticsService.calculate_quality_score(session)
        score = quality.score
        warnings = quality.warnings
        
        # Determine targets
        targets = profiler.target_candidates
        target_str = f"'{targets[0]}'" if targets else "none identified"

        # Check for specific intents:
        # A. Model Recommendations
        if any(kw in msg_lower for kw in ["model", "algorithm", "train", "machine learning", "ml", "predict"]):
            response = (
                f"### Machine Learning Model Recommendations for **{session.filename}**\n\n"
                f"Based on the profiling of your dataset (**{total_rows}** rows, **{total_cols}** columns), "
            )
            
            if targets:
                target_col = targets[0]
                unique_vals = df[target_col].dropna().nunique()
                
                if unique_vals <= 10:
                    # Classification target
                    response += (
                        f"I detected that **{target_col}** is a categorical or discrete variable with {unique_vals} unique classes, "
                        f"which indicates a **Classification** task.\n\n"
                        f"Here are the recommended models:\n"
                        f"1. **Random Forest Classifier**: Excellent baseline for structured data. Handles non-linearities and categorical interactions naturally.\n"
                        f"2. **XGBoost / LightGBM**: State-of-the-art gradient boosters. Recommended if you seek high predictive performance and speed.\n"
                        f"3. **Logistic Regression**: Good if you need a highly explainable model and want to inspect feature coefficients.\n\n"
                        f"**KNN Recommendation Details:**\n"
                        f"- Recommended $K$: {5 if total_rows > 50 else 3}\n"
                        f"- Distance Metric: 'euclidean'\n"
                        f"- Weights: 'uniform'\n"
                    )
                else:
                    # Regression target
                    response += (
                        f"I detected that **{target_col}** is a continuous numerical variable, "
                        f"which indicates a **Regression** task.\n\n"
                        f"Here are the recommended models:\n"
                        f"1. **Random Forest Regressor**: Handles complex multi-feature relationships without overfitting easily.\n"
                        f"2. **XGBoost Regressor**: Outstanding model for complex tabular datasets where you want to minimize mean squared error.\n"
                        f"3. **Ridge / Lasso Regression**: Good standard benchmark if you want linear models with L2/L1 regularization.\n"
                    )
            else:
                response += (
                    "I could not clearly identify a target candidate. If this is an **Unsupervised Learning** task, I recommend:\n"
                    "- **K-Means Clustering** for segmentation (using elbow method to find optimal clusters).\n"
                    "- **Isolation Forest** (already available in the outlier module) for anomaly detection.\n\n"
                    "If you have a supervised learning goal, please specify your target variable (e.g. 'Class', 'Label')."
                )
            return response

        # B. Data Quality / Issues Check
        elif any(kw in msg_lower for kw in ["quality", "score", "issues", "problem", "warnings", "health"]):
            response = (
                f"### Dataset Quality Assessment\n\n"
                f"Your dataset quality score is **{score}/100**.\n\n"
            )
            if warnings:
                response += "I found the following issues that you should address in the preprocessing wizard:\n"
                for w in warnings:
                    response += f"- {w}\n"
                response += "\nTo fix these, head over to the **Duplicates**, **Missing Values**, and **Outliers** sections."
            else:
                response += "Congratulations! The dataset has no immediate critical quality warnings (no duplicates, no severe missingness, no outlier clusters)."
            return response

        # C. Missing values
        elif any(kw in msg_lower for kw in ["missing", "null", "nan", "impute"]):
            missing_recs = RecommendationService.get_missing_recommendations(session)
            if not missing_recs:
                return "Good news! I scanned the dataset and found **no missing values** in any column."
                
            response = "### Missing Values Analysis\n\nI detected missing values in the following columns:\n"
            for rec in missing_recs:
                response += f"- **{rec.column}**: {rec.missing} nulls ({rec.percent}%). *Recommendation:* **{rec.recommended}**.\n"
            response += "\nYou can apply these imputations in the **Missing Values** preprocessing wizard."
            return response

        # D. Outliers
        elif any(kw in msg_lower for kw in ["outlier", "iqr", "zscore", "isolation"]):
            outlier_recs = RecommendationService.get_outlier_recommendations(session)
            if not outlier_recs:
                return "I scanned your numeric columns and found **no significant outliers** using the default IQR thresholds."
                
            response = "### Outliers Analysis\n\nI detected outliers in the following numeric columns:\n"
            for rec in outlier_recs:
                response += (
                    f"- **{rec['column']}**: {rec['outliers']} outlier values ({rec['percentage']}% of rows). "
                    f"*Recommendation:* **{rec['recommended_action']}** using **{rec['recommended_method']}** method.\n"
                )
            response += "\nYou can preview and treat these anomalies in the **Outliers** preprocessor."
            return response

        # E. General Help / Default Response
        else:
            return (
                f"Hello! I am your AI Preprocessing Assistant. I've profiled your dataset: **{session.filename}**.\n\n"
                f"Here is a summary of what I know:\n"
                f"- **Dimensions**: {total_rows} rows × {total_cols} columns\n"
                f"- **Data Types**: {num_cols} numerical features, {cat_cols} categorical features\n"
                f"- **Quality Score**: {score}/100\n"
                f"- **Target Candidates**: {', '.join(targets) if targets else 'None identified'}\n\n"
                f"You can ask me questions like:\n"
                f"- *'Suggest models for my dataset'* (to get recommendations on algorithms)\n"
                f"- *'What are the quality issues?'* (to get warnings and scores)\n"
                f"- *'Show me missing value details'* (to see null columns and recommendations)\n"
                f"- *'Are there outliers?'* (to check for outliers)"
            )
