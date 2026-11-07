import sys
import subprocess

# Usage: python collect_label_retrain.py <person_name>
if len(sys.argv) < 2:
    print("Usage: python collect_label_retrain.py <person_name>")
    sys.exit(1)

person = sys.argv[1]

# Step 1: Label and append new data
echo1 = subprocess.call([sys.executable, 'label_and_append.py', person])
if echo1 != 0:
    print("Labeling/appending failed. Aborting retrain.")
    sys.exit(1)

# Step 2: Retrain the model
echo2 = subprocess.call([sys.executable, 'retrain_model.py'])
if echo2 != 0:
    print("Retraining failed.")
    sys.exit(1)

print("All steps completed: data labeled, appended, and model retrained.")
