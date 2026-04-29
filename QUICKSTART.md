# Quick Start Guide

Get the Early Warning System up and running in minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Generate Sample Data

```bash
python scripts/generate_sample_data.py
```

This creates a synthetic dataset of 1000 students with various academic and behavioral features.

## Step 3: Train the Model

```bash
python ml/train.py
```

This will:
- Train an XGBoost model on the student data
- Generate global explanations
- Evaluate fairness across demographics
- Save the trained model to `data/models/`

**Expected output:**
- Model performance metrics (accuracy, AUC-ROC)
- Top 10 drivers of dropout risk
- Fairness evaluation report

## Step 4: Start the Backend API

```bash
cd backend
uvicorn server:app --reload
```

The API will be available at `http://localhost:8000`

**Test the API:**
```bash
curl http://localhost:8000/health
```

## Step 5: Launch the Dashboard

In a new terminal:

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## What's Next?

### Explore the Dashboard

1. **Overview Page**: View overall statistics and trends
2. **Student Risk Analysis**: 
   - Select a student from the dropdown
   - Click "Predict Dropout Risk"
   - See risk score, category, and top contributing factors
3. **Intervention Tracking**: Record interventions and track outcomes
4. **Fairness Report**: View bias evaluation results

### Make Predictions via API

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU00001",
    "attendance_rate": 0.75,
    "gpa": 2.8,
    "assignment_submission_rate": 0.7,
    "exam_scores": 65,
    "lms_login_frequency": 5,
    "late_submissions": 3,
    "participation_score": 60,
    "forum_posts": 2,
    "resource_access_count": 10,
    "time_spent_hours": 12
  }'
```

### Record an Intervention

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

## Project Structure

```
.
├── ml/                  # Machine learning models and utilities
├── backend/             # FastAPI server
├── dashboard/           # Streamlit dashboard
├── pipelines/           # ETL pipelines
├── data/               # Data storage
│   ├── raw/           # Raw data
│   ├── processed/     # Processed data
│   └── models/         # Trained models
├── configs/            # Configuration files
└── docs/              # Documentation
```

## Troubleshooting

**Model not found error:**
- Make sure you've run `python ml/train.py` first

**API not responding:**
- Check that uvicorn is running: `uvicorn backend.server:app`
- Verify port 8000 is not in use

**Dashboard errors:**
- Ensure backend API is running
- Check that data files exist in `data/raw/`

**Import errors:**
- Make sure all dependencies are installed: `pip install -r requirements.txt`

## Next Steps

- Read `docs/USAGE.md` for detailed usage instructions
- Check `docs/ARCHITECTURE.md` for system architecture
- Customize `configs/model_config.yaml` for your needs
- Add your own data to `data/raw/students.csv`

## Support

For issues or questions, refer to the documentation in the `docs/` directory.
