#!/usr/bin/env bash
# Render build script – runs during the build phase (not at runtime)
# Generates training data and trains the ML model so the artifact is
# baked into the build image.

set -e

echo "=== Render Build: Early Warning System ==="

# Ensure directories exist
mkdir -p data/raw data/models data/processed logs

# Generate training data
echo "--- Generating training data (15,000 students) ---"
python scripts/generate_enhanced_data.py

# Train the model
echo "--- Training XGBoost model ---"
python ml/train.py

# Verify model artifacts exist
echo "--- Verifying model artifacts ---"
ls -lh data/models/

echo "=== Build complete ==="
