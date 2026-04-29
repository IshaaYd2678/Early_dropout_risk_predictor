"""
Enhanced FastAPI backend server that supports frontend integration.
Provides API endpoints matching frontend expectations.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import pandas as pd
from pathlib import Path
import sys
import json
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ml.predict import DropoutRiskPredictor
from backend.interventions import InterventionTracker, Intervention

app = FastAPI(
    title="Student Retention Platform API",
    description="Enhanced API for student dropout risk prediction with frontend integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8503"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize components
try:
    predictor = DropoutRiskPredictor()
    model_loaded = True
except FileNotFoundError:
    predictor = None
    model_loaded = False
    print("Warning: Model not found. Please train the model first.")

intervention_tracker = InterventionTracker()

# Mock data for demo
MOCK_STUDENTS = []
MOCK_USERS = [
    {
        "id": "user1",
        "email": "admin@university.edu",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "tenant_id": "tenant1"
    }
]

# Load student data if available
try:
    df = pd.read_csv("data/raw/students.csv")
    for _, row in df.head(50).iterrows():  # Limit to 50 for demo
        student = {
            "id": f"student_{row.name}",
            "student_id": f"STU{row.name:05d}",
            "first_name": f"Student",
            "last_name": f"{row.name}",
            "email": f"student{row.name}@university.edu",
            "department": row.get("department", "Unknown"),
            "program": "Bachelor's",
            "semester": int(row.get("semester", 1)),
            "status": "active",
            "current_risk_level": None,
            "current_risk_score": None,
            "requires_attention": False,
            "intervention_active": False,
            "mentor_id": None,
            "created_at": datetime.now().isoformat(),
            # Academic metrics
            "gpa": row.get("gpa"),
            "attendance_rate": row.get("attendance_rate"),
            "assignment_submission_rate": row.get("assignment_submission_rate"),
            "late_submissions": int(row.get("late_submissions", 0)),
            "lms_login_frequency": int(row.get("lms_login_frequency", 0)),
            "forum_posts": int(row.get("forum_posts", 0)),
            "resource_access_count": int(row.get("resource_access_count", 0)),
            "time_spent_hours": row.get("time_spent_hours"),
            "participation_score": row.get("participation_score"),
            "exam_scores": row.get("exam_scores"),
            "gender": row.get("gender"),
            "socioeconomic_status": row.get("socioeconomic_status"),
            "region": row.get("region"),
        }
        MOCK_STUDENTS.append(student)
except Exception as e:
    print(f"Could not load student data: {e}")

# Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    tenant_id: str

class StudentResponse(BaseModel):
    id: str
    student_id: str
    first_name: str
    last_name: str
    email: Optional[str]
    department: str
    program: Optional[str]
    semester: int
    status: str
    current_risk_level: Optional[str]
    current_risk_score: Optional[float]
    requires_attention: bool
    intervention_active: bool
    mentor_id: Optional[str]
    created_at: str

class StudentDetailResponse(StudentResponse):
    gpa: Optional[float]
    attendance_rate: Optional[float]
    assignment_submission_rate: Optional[float]
    late_submissions: int
    lms_login_frequency: int
    forum_posts: int
    resource_access_count: int
    time_spent_hours: Optional[float]
    participation_score: Optional[float]
    exam_scores: Optional[float]
    gender: Optional[str]
    socioeconomic_status: Optional[str]
    region: Optional[str]

class StudentListResponse(BaseModel):
    items: List[StudentResponse]
    total: int
    page: int
    page_size: int
    pages: int

class PredictionRequest(BaseModel):
    student_id: str

class FactorContribution(BaseModel):
    feature: str
    contribution: float
    direction: str
    value: Optional[float] = None

class PredictionResponse(BaseModel):
    student_id: str
    risk_score: float
    risk_level: str
    confidence: Optional[float] = None
    top_factors: List[FactorContribution]
    explanation: str
    model_version: str
    predicted_at: str

# Mock authentication
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # For demo purposes, return mock user
    return MOCK_USERS[0]

# API Routes

@app.get("/")
async def root():
    return {
        "name": "Student Retention Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "students_loaded": len(MOCK_STUDENTS)
    }

# Auth endpoints
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    # Mock authentication - accept any email/password for demo
    return TokenResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        expires_in=1800
    )

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# Student endpoints
@app.get("/api/v1/students", response_model=StudentListResponse)
async def list_students(
    page: int = 1,
    page_size: int = 20,
    department: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    students = MOCK_STUDENTS.copy()
    
    # Apply filters
    if department:
        students = [s for s in students if s["department"] == department]
    if risk_level:
        students = [s for s in students if s.get("current_risk_level") == risk_level]
    if search:
        search_lower = search.lower()
        students = [s for s in students if 
                   search_lower in s["first_name"].lower() or 
                   search_lower in s["last_name"].lower() or 
                   search_lower in s["student_id"].lower()]
    
    total = len(students)
    start = (page - 1) * page_size
    end = start + page_size
    page_students = students[start:end]
    
    return StudentListResponse(
        items=[StudentResponse(**s) for s in page_students],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )

@app.get("/api/v1/students/{student_id}", response_model=StudentDetailResponse)
async def get_student(
    student_id: str,
    current_user: dict = Depends(get_current_user)
):
    student = next((s for s in MOCK_STUDENTS if s["id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return StudentDetailResponse(**student)

@app.get("/api/v1/students/stats/summary")
async def get_students_summary(current_user: dict = Depends(get_current_user)):
    total = len(MOCK_STUDENTS)
    
    # Risk distribution
    risk_counts = {}
    attention_count = 0
    for student in MOCK_STUDENTS:
        risk_level = student.get("current_risk_level", "unknown")
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
        if student.get("requires_attention"):
            attention_count += 1
    
    # Department distribution
    dept_counts = {}
    for student in MOCK_STUDENTS:
        dept = student["department"]
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
    
    return {
        "total_students": total,
        "risk_distribution": risk_counts,
        "requires_attention": attention_count,
        "by_department": dept_counts
    }

# Prediction endpoints
@app.post("/api/v1/predictions/single", response_model=PredictionResponse)
async def predict_single(
    data: PredictionRequest,
    current_user: dict = Depends(get_current_user)
):
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Find student
    student = next((s for s in MOCK_STUDENTS if s["id"] == data.student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Prepare data for prediction
    student_data = {
        "attendance_rate": student.get("attendance_rate", 0.8),
        "gpa": student.get("gpa", 3.0),
        "assignment_submission_rate": student.get("assignment_submission_rate", 0.9),
        "exam_scores": student.get("exam_scores", 75),
        "lms_login_frequency": student.get("lms_login_frequency", 10),
        "late_submissions": student.get("late_submissions", 2),
        "participation_score": student.get("participation_score", 80),
        "forum_posts": student.get("forum_posts", 5),
        "resource_access_count": student.get("resource_access_count", 20),
        "time_spent_hours": student.get("time_spent_hours", 15),
        "gender": student.get("gender", "Unknown"),
        "department": student.get("department", "Unknown"),
        "socioeconomic_status": student.get("socioeconomic_status", "Unknown"),
        "region": student.get("region", "Unknown"),
        "semester": student.get("semester", 1)
    }
    
    # Make prediction
    result = predictor.predict(student_data, include_explanation=True)
    
    # Update student record
    for s in MOCK_STUDENTS:
        if s["id"] == data.student_id:
            s["current_risk_score"] = result["risk_score"]
            s["current_risk_level"] = result["risk_category"].lower()
            s["requires_attention"] = result["risk_category"].lower() in ["high", "critical"]
            break
    
    # Format factors
    factors = []
    if "explanation" in result and "feature_contributions" in result["explanation"]:
        for feature, contrib in result["explanation"]["feature_contributions"].items():
            factors.append(FactorContribution(
                feature=feature,
                contribution=abs(contrib),
                direction="increases" if contrib > 0 else "decreases",
                value=student_data.get(feature)
            ))
    
    return PredictionResponse(
        student_id=data.student_id,
        risk_score=result["risk_score"],
        risk_level=result["risk_category"].lower(),
        top_factors=factors[:5],  # Top 5 factors
        explanation=f"Student has {result['risk_category'].lower()} dropout risk based on academic and engagement metrics.",
        model_version="1.0.0",
        predicted_at=datetime.now().isoformat()
    )

@app.get("/api/v1/predictions/model/info")
async def get_model_info(current_user: dict = Depends(get_current_user)):
    if not model_loaded:
        return {"model_available": False, "message": "No model currently deployed"}
    
    return {
        "model_available": True,
        "version": "1.0.0",
        "deployed_at": datetime.now().isoformat(),
        "accuracy": 0.63,
        "auc_roc": 0.66,
        "fairness_metrics": {"demographic_parity": 0.85},
        "bias_detected": False,
        "feature_importance": {
            "assignment_submission_rate": 0.25,
            "gpa": 0.20,
            "attendance_rate": 0.18,
            "forum_posts": 0.12,
            "exam_scores": 0.10
        }
    }

# Analytics endpoints
@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_analytics(current_user: dict = Depends(get_current_user)):
    total_students = len(MOCK_STUDENTS)
    high_risk = len([s for s in MOCK_STUDENTS if s.get("current_risk_level") == "high"])
    
    return {
        "total_students": total_students,
        "high_risk_students": high_risk,
        "interventions_active": 5,
        "success_rate": 0.78,
        "trends": {
            "risk_trend": [0.15, 0.18, 0.16, 0.14, 0.12],
            "intervention_effectiveness": 0.82
        }
    }

# Intervention endpoints
@app.get("/api/v1/interventions")
async def list_interventions(
    student_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        df = intervention_tracker.get_interventions(student_id)
        if df.empty:
            return {"interventions": [], "count": 0}
        return {"interventions": df.to_dict('records'), "count": len(df)}
    except Exception as e:
        return {"interventions": [], "count": 0}

@app.post("/api/v1/interventions")
async def create_intervention(
    intervention: Intervention,
    current_user: dict = Depends(get_current_user)
):
    try:
        intervention_id = intervention_tracker.add_intervention(intervention)
        return {"message": "Intervention created successfully", "id": intervention_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)