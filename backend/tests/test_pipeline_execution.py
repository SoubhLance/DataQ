import os
import subprocess
import pytest
import pandas as pd
import sys

@pytest.mark.integration
def test_pipeline_execution_flow(client, create_temp_file, tmp_path):
    """
    Test codegen validation:
    1. Upload a dataset.
    2. Apply some preprocessing steps (drop columns, missing imputation, scaling).
    3. Generate the Pandas script.
    4. Save the script to a file.
    5. Run the script in a subprocess and verify returncode == 0.
    """
    # Create dataset
    df_original = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25.0, 30.0, None, 40.0, 35.0],
        "salary": [50000.0, 60000.0, 55000.0, 80000.0, 120000.0] # 120000 is an outlier
    })
    
    # Save to a temporary location using a fixed name that codegen will use
    filename = "input_pipeline_test.csv"
    input_filepath = os.path.join(tmp_path, filename)
    df_original.to_csv(input_filepath, index=False)
    
    # Upload to API
    with open(input_filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    assert upload_res.status_code == 200
    session_id = upload_res.json()["session_id"]
    
    # Apply Operation 1: Drop 'name' column
    res1 = client.post(
        "/api/v1/columns/drop",
        json={"session_id": session_id, "columns": ["name"]}
    )
    assert res1.status_code == 200
    
    # Apply Operation 2: Impute 'age' column with mean
    res2 = client.post(
        "/api/v1/missing/apply",
        json={"session_id": session_id, "column": "age", "strategy": "mean"}
    )
    assert res2.status_code == 200
    
    # Apply Operation 3: Scale 'salary' using standard scaling
    res3 = client.post(
        "/api/v1/scaling/apply",
        json={"session_id": session_id, "columns": ["salary"], "method": "standard"}
    )
    assert res3.status_code == 200
    
    # Get pipeline script
    pipeline_res = client.get(f"/api/v1/pipeline/{session_id}?format=pandas")
    assert pipeline_res.status_code == 200
    pipeline_code = pipeline_res.json()["pipeline"]
    
    # Write code to a file in the tmp_path directory
    script_filepath = os.path.join(tmp_path, "generated_pipeline.py")
    with open(script_filepath, "w") as sf:
        sf.write(pipeline_code)
        
    # Execute the generated script in a subprocess
    # Run using the same python executable to ensure pandas/sklearn dependencies are present
    run_res = subprocess.run(
        [sys.executable, "generated_pipeline.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    
    # Print outputs in case of failure for debugging
    print("STDOUT:", run_res.stdout)
    print("STDERR:", run_res.stderr)
    
    assert run_res.returncode == 0
    
    # Verify that the output 'cleaned_dataset.csv' was created
    output_filepath = os.path.join(tmp_path, "cleaned_dataset.csv")
    assert os.path.exists(output_filepath)
    
    # Check shape of clean dataframe
    df_cleaned = pd.read_csv(output_filepath)
    assert "name" not in df_cleaned.columns
    assert df_cleaned["age"].isna().sum() == 0

@pytest.mark.integration
def test_pipeline_formats(client, create_temp_file):
    """Test retrieving pipeline in different formats (sklearn, notebook, yaml) to cover codegen and raise coverage."""
    filepath = create_temp_file(".csv")
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload",
            files={"file": (filename, f, "text/csv")}
        )
    session_id = upload_res.json()["session_id"]
    
    # Apply some operations to populate history
    client.post("/api/v1/columns/drop", json={"session_id": session_id, "columns": ["name"]})
    client.post("/api/v1/missing/apply", json={"session_id": session_id, "column": "age", "strategy": "mean"})
    client.post("/api/v1/columns/encode", json={"session_id": session_id, "column": "gender", "method": "onehot"})
    client.post("/api/v1/scaling/apply", json={"session_id": session_id, "columns": ["salary"], "method": "minmax"})
    
    # 1. Sklearn
    res_sklearn = client.get(f"/api/v1/pipeline/{session_id}?format=sklearn")
    assert res_sklearn.status_code == 200
    data_sklearn = res_sklearn.json()
    assert "ColumnTransformer" in data_sklearn["pipeline"]
    assert "Pipeline" in data_sklearn["pipeline"]
    assert data_sklearn["format"] == "sklearn"
    
    # 2. Notebook
    res_notebook = client.get(f"/api/v1/pipeline/{session_id}?format=notebook")
    assert res_notebook.status_code == 200
    data_notebook = res_notebook.json()
    assert "nbformat" in data_notebook["pipeline"]
    assert data_notebook["format"] == "notebook"
    
    # 3. YAML
    res_yaml = client.get(f"/api/v1/pipeline/{session_id}?format=yaml")
    assert res_yaml.status_code == 200
    data_yaml = res_yaml.json()
    assert "pipeline:" in data_yaml["pipeline"]
    assert "version:" in data_yaml["pipeline"]
    assert data_yaml["format"] == "yaml"

