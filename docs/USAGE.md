# Usage Guide

## Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Generate Sample Data**
```bash
python scripts/generate_sample_data.py
```

3. **Process Data**
```bash
python pipelines/data_pipeline.py
```

## Training Models

### Basic Training
```bash
python ml/train.py
```

This will:
- Load student data
- Train the model (XGBoost by default)
- Generate global explanations
- Evaluate fairness
- Save model artifacts
- Generate fairness report

### Model Configuration

Edit `configs/model_config.yaml` to:
- Change model type (xgboost, logistic_regression, decision_tree)
- Adjust risk thresholds
- Modify training parameters
- Configure fairness evaluation

## Making Predictions

### Python API
```python
from ml.predict import DropoutRiskPredictor

# Initialize predictor
predictor = DropoutRiskPredictor()

# Predict for a single student
student_data = {
    'student_id': 'STU00001',
    'gender': 'Male',
    'department': 'Computer Science',
    'attendance_rate': 0.75,
    'gpa': 2.8,
    # ... other features
}

result = predictor.predict(student_data)
print(f"Risk Score: {result['risk_score']:.2%}")
print(f"Risk Category: {result['risk_category']}")
print(f"Top Factors: {result['explanation']['top_factors']}")
```

### REST API

1. **Start Backend Server**
```bash
cd backend
uvicorn server:app --reload
```

2. **Make Prediction Request**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU00001",
    "attendance_rate": 0.75,
    "gpa": 2.8,
    ...
  }'
```

## Using the Dashboard

1. **Start Dashboard**
```bash
streamlit run dashboard/app.py
```

2. **Navigate Pages**
   - **Overview**: View overall statistics and trends
   - **Student Risk Analysis**: Predict risk for individual students
   - **Intervention Tracking**: Record and monitor interventions
   - **Fairness Report**: View bias evaluation results

## Intervention Tracking

### Record Intervention via API
```bash
curl -X POST "http://localhost:8000/interventions" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU00001",
    "intervention_type": "Counseling",
    "date": "2026-01-29",
    "notes": "Initial counseling session",
    "outcome": "pending"
  }'
```

### View Interventions
```bash
curl "http://localhost:8000/interventions?student_id=STU00001"
```

### Update Outcome
```bash
curl -X PUT "http://localhost:8000/interventions/1/outcome?outcome=risk_reduced"
```

## Fairness Evaluation

After training, view the fairness report:
```bash
cat data/fairness_report.txt
```

The report includes:
- Overall model performance
- Group-level metrics by sensitive attribute
- Fairness metrics (Demographic Parity, Equalized Odds)
- Bias detection results

## Batch Processing

### Batch Predictions
```python
import pandas as pd
from ml.predict import DropoutRiskPredictor

predictor = DropoutRiskPredictor()
df = pd.read_csv('data/raw/students.csv')

# Predict for all students
results = predictor.predict(df, include_explanation=True)
```

### Batch via API
```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d @students_batch.json
```

## Model Retraining

To retrain with new data:
1. Update data in `data/raw/students.csv`
2. Run `python pipelines/data_pipeline.py` to process
3. Run `python ml/train.py` to retrain
4. Model artifacts will be updated automatically

## Customization

### Adding New Features
1. Update feature list in `configs/model_config.yaml`
2. Ensure data pipeline generates the feature
3. Retrain model

### Changing Risk Thresholds
Edit `configs/model_config.yaml`:
```yaml
model:
  risk_thresholds:
    low: 0.3
    medium: 0.6
    high: 0.8
```

### Adding New Sensitive Attributes
Update fairness configuration:
```yaml
fairness:
  sensitive_attributes:
    - gender
    - socioeconomic_status
    - department
    - region
    - new_attribute
```

## Troubleshooting

### Model Not Found
- Ensure you've run `python ml/train.py` first
- Check that model files exist in `data/models/`

### API Not Responding
- Verify backend server is running: `uvicorn backend.server:app`
- Check port 8000 is available

### Dashboard Errors
- Ensure backend API is running
- Check data files exist in `data/raw/`

### SHAP Errors
- Ensure model is trained
- Check feature names match between training and prediction
