"""
FastAPI backend server for dropout risk prediction API.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ml.predict import DropoutRiskPredictor
from backend.interventions import InterventionTracker, Intervention

app = FastAPI(
    title="Early Warning System API",
    description="API for student dropout risk prediction",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor
try:
    # Use absolute paths relative to project root
    project_root = Path(__file__).parent.parent
    model_path = project_root / "data" / "models" / "xgboost_model.pkl"
    feature_names_path = project_root / "data" / "models" / "feature_names.pkl"
    predictor = DropoutRiskPredictor(
        model_path=str(model_path),
        feature_names_path=str(feature_names_path)
    )
    print(f"Model loaded successfully from {model_path}")
except FileNotFoundError as e:
    predictor = None
    print(f"Warning: Model not found. {e}")
    print("Please train the model first using: python ml/train.py")

# Initialize intervention tracker
intervention_tracker = InterventionTracker()

class StudentData(BaseModel):
    """Student data model for prediction."""
    student_id: Optional[str] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    region: Optional[str] = None
    socioeconomic_status: Optional[str] = None
    semester: Optional[int] = None
    attendance_rate: Optional[float] = None
    gpa: Optional[float] = None
    assignment_submission_rate: Optional[float] = None
    exam_scores: Optional[float] = None
    lms_login_frequency: Optional[int] = None
    late_submissions: Optional[int] = None
    participation_score: Optional[float] = None
    forum_posts: Optional[int] = None
    resource_access_count: Optional[int] = None
    time_spent_hours: Optional[float] = None

class PredictionResponse(BaseModel):
    """Prediction response model."""
    student_id: Optional[str]
    risk_score: float
    risk_category: str
    explanation: Optional[dict] = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Early Warning System API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "predict_batch": "/predict/batch",
            "health": "/health",
            "interventions": "/interventions",
            "intervention_stats": "/interventions/stats"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": predictor is not None
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_risk(student: StudentData):
    """Predict dropout risk for a single student."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    try:
        # Convert to dict
        student_dict = student.dict(exclude_none=True)
        
        # Predict
        result = predictor.predict(student_dict, include_explanation=True)
        
        return PredictionResponse(
            student_id=student_dict.get('student_id'),
            risk_score=result['risk_score'],
            risk_category=result['risk_category'],
            explanation=result.get('explanation')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/predict/batch")
async def predict_batch(students: List[StudentData]):
    """Predict dropout risk for multiple students."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    try:
        # Convert to DataFrame
        students_dict = [s.dict(exclude_none=True) for s in students]
        df = pd.DataFrame(students_dict)
        
        # Predict
        results = predictor.predict(df, include_explanation=True)
        
        # Format response
        predictions = []
        risk_scores = results['risk_score'] if isinstance(results['risk_score'], list) else [results['risk_score']]
        risk_categories = results['risk_category'] if isinstance(results['risk_category'], list) else [results['risk_category']]
        explanations = results.get('explanations', [])
        
        for i, (score, category) in enumerate(zip(risk_scores, risk_categories)):
            pred = {
                "student_id": students_dict[i].get('student_id'),
                "risk_score": score,
                "risk_category": category
            }
            if explanations and i < len(explanations):
                pred["explanation"] = explanations[i]
            predictions.append(pred)
        
        return {"predictions": predictions, "count": len(predictions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")

@app.post("/interventions")
async def add_intervention(intervention: Intervention):
    """Add a new intervention."""
    try:
        intervention_id = intervention_tracker.add_intervention(intervention)
        return {"message": "Intervention added successfully", "intervention_id": intervention_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding intervention: {str(e)}")

@app.get("/interventions")
async def get_interventions(student_id: Optional[str] = None):
    """Get interventions, optionally filtered by student_id."""
    try:
        df = intervention_tracker.get_interventions(student_id)
        if df.empty:
            return {"interventions": [], "count": 0}
        return {"interventions": df.to_dict('records'), "count": len(df)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving interventions: {str(e)}")

@app.put("/interventions/{intervention_id}/outcome")
async def update_intervention_outcome(intervention_id: int, outcome: str):
    """Update intervention outcome."""
    try:
        intervention_tracker.update_outcome(intervention_id, outcome)
        return {"message": "Outcome updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating outcome: {str(e)}")

@app.get("/interventions/stats")
async def get_intervention_stats():
    """Get intervention statistics."""
    try:
        stats = intervention_tracker.get_intervention_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
