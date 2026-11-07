import os
import sys
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

# Usage: python retrain_model.py [notebook_path]
notebook_path = sys.argv[1] if len(sys.argv) > 1 else 'neuratrack_working.ipynb'

if not os.path.exists(notebook_path):
    print(f"Notebook {notebook_path} not found.")
    sys.exit(1)

with open(notebook_path) as f:
    nb = nbformat.read(f, as_version=4)

print(f"Running notebook: {notebook_path}")

# Execute the notebook
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
ep.preprocess(nb, {'metadata': {'path': os.path.dirname(notebook_path) or '.'}})

print("Retraining complete. Artifacts updated.")
