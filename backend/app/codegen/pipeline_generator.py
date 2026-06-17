import json
from typing import List, Dict, Any
from app.models.operation_model import Operation

class PipelineGenerator:
    """
    Code generator that translates a sequence of operations into multiple formats:
    Pandas python scripts, sklearn Pipeline definitions, Jupyter Notebooks, and YAML recipes.
    """
    
    @staticmethod
    def generate_pandas_script(filename: str, operations: List[Operation]) -> str:
        """Generate a complete standalone Pandas Python script."""
        imports = [
            "import pandas as pd",
            "import numpy as np",
        ]
        
        # Check if sklearn imports are needed based on operations
        need_label_encoder = any(op.type == "column_encode" and op.params.get("method") == "label" for op in operations)
        need_scaler = any(op.type == "scaling" for op in operations)
        need_iforest = any(op.type == "outliers" and op.params.get("method") == "iforest" for op in operations)
        
        if need_label_encoder:
            imports.append("from sklearn.preprocessing import LabelEncoder")
        if need_scaler:
            # Dynamically check which scalers are used
            scalers = set()
            for op in operations:
                if op.type == "scaling":
                    method = op.params.get("method")
                    if method == "standard":
                        scalers.add("StandardScaler")
                    elif method == "minmax":
                        scalers.add("MinMaxScaler")
                    elif method == "robust":
                        scalers.add("RobustScaler")
            if scalers:
                imports.append(f"from sklearn.preprocessing import {', '.join(sorted(scalers))}")
        if need_iforest:
            imports.append("from sklearn.ensemble import IsolationForest")
            
        header = "\n".join(imports) + "\n\n"
        
        # Load script
        loader = f"# 1. Load Dataset\ndf = pd.read_csv('{filename}')\n\n"
        
        # Steps
        steps_code = "# 2. Preprocessing Steps\n"
        if not operations:
            steps_code += "# No operations were applied.\npass\n"
        for idx, op in enumerate(operations, 1):
            steps_code += f"# Step {idx}: {op.type} ({op.params})\n"
            steps_code += op.generated_code + "\n\n"
            
        # Saver
        saver = "# 3. Export Cleaned Dataset\ndf.to_csv('cleaned_dataset.csv', index=False)\nprint('Data cleaning pipeline executed successfully. Output saved to cleaned_dataset.csv.')\n"
        
        return header + loader + steps_code + saver

    @staticmethod
    def generate_sklearn_pipeline(operations: List[Operation]) -> str:
        """Generate a Scikit-Learn Pipeline and ColumnTransformer blueprint."""
        # Find features subject to specific operations
        num_impute_cols = {}
        cat_impute_cols = {}
        scaling_cols = {}
        scaling_method = "standard"
        encode_label_cols = []
        encode_onehot_cols = []
        drop_cols = []
        
        for op in operations:
            if op.type == "column_drop":
                drop_cols.extend(op.params.get("columns", []))
            elif op.type == "missing":
                col = op.params.get("column")
                strategy = op.params.get("strategy")
                if strategy in ["mean", "median"]:
                    num_impute_cols[col] = strategy
                elif strategy == "mode":
                    cat_impute_cols[col] = "most_frequent"
                elif strategy == "constant":
                    cat_impute_cols[col] = "constant"
            elif op.type == "scaling":
                cols = op.params.get("columns", [])
                method = op.params.get("method", "standard")
                scaling_method = method
                for c in cols:
                    scaling_cols[c] = method
            elif op.type == "column_encode":
                col = op.params.get("column")
                method = op.params.get("method")
                if method == "label":
                    encode_label_cols.append(col)
                elif method == "onehot":
                    encode_onehot_cols.append(col)
                    
        # Map scaling classes
        scaler_mapping = {
            "standard": "StandardScaler()",
            "minmax": "MinMaxScaler()",
            "robust": "RobustScaler()"
        }
        scaler_class = scaler_mapping.get(scaling_method, "StandardScaler()")
        
        # Build generated python script code
        code = (
            "import pandas as pd\n"
            "import numpy as np\n"
            "from sklearn.compose import ColumnTransformer\n"
            "from sklearn.pipeline import Pipeline\n"
            "from sklearn.impute import SimpleImputer\n"
            "from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, OneHotEncoder, OrdinalEncoder\n\n"
            "# 1. Define Column Subsets based on Preprocessing History\n"
        )
        
        # Lists
        code += f"dropped_columns = {drop_cols}\n"
        code += f"numeric_impute_cols = {list(num_impute_cols.keys())}\n"
        code += f"categorical_impute_cols = {list(cat_impute_cols.keys())}\n"
        code += f"scaled_columns = {list(scaling_cols.keys())}\n"
        code += f"onehot_encoded_columns = {encode_onehot_cols}\n"
        code += f"label_encoded_columns = {encode_label_cols}\n\n"
        
        # Numeric pipeline
        code += (
            "# 2. Build Feature-Specific Pipeline Blocks\n"
            "numeric_transformer = Pipeline(steps=[\n"
            "    ('imputer', SimpleImputer(strategy='median')),\n"
            f"    ('scaler', {scaler_class})\n"
            "])\n\n"
            "categorical_transformer = Pipeline(steps=[\n"
            "    ('imputer', SimpleImputer(strategy='most_frequent')),\n"
            "    ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))\n"
            "])\n\n"
        )
        
        # Column transformer
        code += (
            "# 3. Combine in a ColumnTransformer\n"
            "preprocessor = ColumnTransformer(\n"
            "    transformers=[\n"
            "        ('num', numeric_transformer, numeric_impute_cols + scaled_columns),\n"
            "        ('cat', categorical_transformer, categorical_impute_cols + onehot_encoded_columns)\n"
            "    ],\n"
            "    remainder='passthrough'  # Keep remaining columns intact\n"
            ")\n\n"
            "# 4. Final ML Pipeline\n"
            "pipeline = Pipeline(steps=[\n"
            "    ('preprocessor', preprocessor)\n"
            "])\n\n"
            "print('Scikit-Learn Pipeline constructed successfully:')\n"
            "print(pipeline)\n"
        )
        
        return code

    @staticmethod
    def generate_jupyter_notebook(filename: str, operations: List[Operation]) -> str:
        """Generate a Jupyter Notebook (.ipynb JSON structure)."""
        cells = []
        
        # Title
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Data Preprocessing & Cleaning Pipeline\n",
                "This notebook reproduces the data cleaning operations applied during the session."
            ]
        })
        
        # Setup Cell
        imports_code = [
            "import pandas as pd\n",
            "import numpy as np\n"
        ]
        need_label_encoder = any(op.type == "column_encode" and op.params.get("method") == "label" for op in operations)
        need_scaler = any(op.type == "scaling" for op in operations)
        if need_label_encoder:
            imports_code.append("from sklearn.preprocessing import LabelEncoder\n")
        if need_scaler:
            imports_code.append("from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler\n")
            
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": imports_code
        })
        
        # Load Dataset
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Load Dataset"]
        })
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [f"df = pd.read_csv('{filename}')\ndf.head()"]
        })
        
        # Operations
        if operations:
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## Preprocessing Steps"]
            })
            
            for idx, op in enumerate(operations, 1):
                cells.append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [f"### Step {idx}: {op.type.capitalize()}\n", f"Parameters: `{op.params}`"]
                })
                # Split code by line breaks and append \n
                code_lines = [line + "\n" for line in op.generated_code.split("\n")]
                # Add a df.head() display
                code_lines.append("\ndf.head()")
                
                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": code_lines
                })
        
        # Export Cell
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Export Cleaned Data"]
        })
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["df.to_csv('cleaned_dataset.csv', index=False)\nprint('Cleaned dataset saved.')"]
        })
        
        notebook = {
            "cells": cells,
            "metadata": {
                "language_info": {
                    "name": "python"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 2
        }
        
        return json.dumps(notebook, indent=2)

    @staticmethod
    def generate_yaml_recipe(operations: List[Operation]) -> str:
        """Generate a YAML configuration recipe."""
        recipe_dict = {
            "version": "1.0",
            "pipeline": []
        }
        
        for idx, op in enumerate(operations):
            recipe_dict["pipeline"].append({
                "step": idx + 1,
                "type": op.type,
                "parameters": op.params
            })
            
        # Basic YAML dumper (avoiding PyYAML dependency)
        yaml_lines = ["version: '1.0'", "pipeline:"]
        for step in recipe_dict["pipeline"]:
            yaml_lines.append(f"  - step: {step['step']}")
            yaml_lines.append(f"    type: {step['type']}")
            yaml_lines.append("    parameters:")
            for k, v in step["parameters"].items():
                val_str = f"'{v}'" if isinstance(v, str) else str(v)
                yaml_lines.append(f"      {k}: {val_str}")
                
        return "\n".join(yaml_lines)
