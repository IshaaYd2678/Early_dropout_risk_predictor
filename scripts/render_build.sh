#!/usr/bin/env bash
# Render build script – generates data and trains the ML model.
set -e

echo "=== Render Build: Early Warning System ==="

mkdir -p data/raw data/models data/processed logs

# Use a smaller dataset on Render free tier to avoid OOM during build
echo "--- Generating training data ---"
python - <<'EOF'
import sys
sys.path.insert(0, ".")
from scripts.generate_enhanced_data import generate_realistic_student_data
from pathlib import Path
import pandas as pd

# 5,000 students is enough to train a good model and stays within free-tier RAM
df = generate_realistic_student_data(n_students=5000)
out = Path("data/raw/students.csv")
df.to_csv(out, index=False)
print(f"Generated {len(df)} student records → {out}")
print(f"Dropout rate: {df['dropped_out'].mean():.2%}")
EOF

echo "--- Training XGBoost model ---"
python ml/train.py

echo "--- Verifying model artifacts ---"
ls -lh data/models/

echo "=== Build complete ==="
