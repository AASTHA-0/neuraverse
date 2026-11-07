import pandas as pd
import sys
from pathlib import Path

# Usage: python label_and_append.py <person_name>
if len(sys.argv) < 2:
    print("Usage: python label_and_append.py <person_name>")
    sys.exit(1)

person = sys.argv[1]

# File paths
realtime_file = 'eeg_realtime.csv'
labeled_file = 'eeg_labeled.csv'

# Load real-time data
if not Path(realtime_file).exists():
    print(f"{realtime_file} not found.")
    sys.exit(1)

df_new = pd.read_csv(realtime_file)
if df_new.empty:
    print("No new data to label.")
    sys.exit(0)

# Add/overwrite person column
print(f"Labeling {len(df_new)} rows as '{person}'...")
df_new['person'] = person

# Append to labeled file
if Path(labeled_file).exists():
    df_labeled = pd.read_csv(labeled_file)
    df_combined = pd.concat([df_labeled, df_new], ignore_index=True)
else:
    df_combined = df_new

df_combined.to_csv(labeled_file, index=False)
print(f"Appended to {labeled_file}.")

# Optionally clear real-time file
df_new.iloc[0:0].to_csv(realtime_file, index=False)
print(f"Cleared {realtime_file}.")
