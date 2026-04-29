"""
Risk prediction endpoints.
AI-powered dropout risk assessment with explanations.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, CurrentTenant, DBSession
from src.models.student import Student, StudentRiskScore, RiskLevel
from src.models.ml_model import Prediction, ModelVersion, ModelStatus
from src.services.ml.predictor import RiskPredictor
from src.services.audit import create_audit_log
from src.models.audit import AuditAction


router = APIRouter()


# Schemas
class PredictionRequest(BaseModel):
    """Single prediction request."""
    student_id: str


class BatchPredictionRequest(BaseModel):
    """Batch prediction request."""
    student_ids: List[str] = Field(..., max_length=100)


class FactorContribution(BaseModel):
    """Risk factor contribution."""
    feature: str
    contribution: float
    direction: str  # "increases" or "decreases"
    value: Optional[float] = None


class PredictionResponse(BaseModel):
    """Prediction response with explanation."""
    student_id: str
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: RiskLevel
    confidence: Optional[float] = None
    top_factors: List[FactorContribution]
    explanation: str
    model_version: str
    predicted_at: datetime


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""
    predictions: List[PredictionResponse]
    total: int
    successful: int
    failed: int
    errors: List[dict] = []


class GlobalInsightsResponse(BaseModel):
    """Global model insights."""
    top_risk_drivers: List[dict]
    department_insights: dict
    semester_insights: dict
    model_performance: dict


@router.post("/single", response_model=PredictionResponse)
async def predict_single(
    data: PredictionRequest,
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
    background_tasks: BackgroundTasks,
):
    """
    Predict dropout risk for a single student.
    Returns risk score, level, and explanations.
    """
    # Get student
    result = await db.execute(
        select(Student).where(
            Student.id == data.student_id,
            Student.tenant_id == tenant.id,
            Student.is_deleted == False
        )
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get predictor
    predictor = RiskPredictor(tenant_id=tenant.id)
    
    # Make prediction
    prediction = await predictor.predict(student, db)
    
    # Save to history
    risk_score_record = StudentRiskScore(
        tenant_id=tenant.id,
        student_id=student.id,
        model_version_id=prediction.get("model_version_id"),
        risk_score=prediction["risk_score"],
        risk_level=RiskLevel(prediction["risk_level"]),
        confidence=prediction.get("confidence"),
        top_factors={"factors": prediction["top_factors"]},
        all_contributions=prediction.get("all_contributions", {}),
        explanation_text=prediction["explanation"],
        semester=student.semester,
    )
    db.add(risk_score_record)
    
    # Update student's current risk
    student.current_risk_score = prediction["risk_score"]
    student.current_risk_level = RiskLevel(prediction["risk_level"])
    student.risk_updated_at = datetime.utcnow()
    student.requires_attention = prediction["risk_level"] in ["high", "critical"]
    
    await db.commit()
    
    # Audit log
    background_tasks.add_task(
        create_audit_log,
        db=db,
        action=AuditAction.PREDICTION_MADE,
        user_id=current_user.id,
        tenant_id=tenant.id,
        resource_type="student",
        resource_id=student.id,
        description=f"Risk prediction for student {student.student_id}",
        details={"risk_level": prediction["risk_level"], "risk_score": prediction["risk_score"]}
    )
    
    return PredictionResponse(
        student_id=student.id,
        risk_score=prediction["risk_score"],
        risk_level=RiskLevel(prediction["risk_level"]),
        confidence=prediction.get("confidence"),
        top_factors=[
            FactorContribution(**f) for f in prediction["top_factors"]
        ],
        explanation=prediction["explanation"],
        model_version=prediction.get("model_version", "1.0.0"),
        predicted_at=datetime.utcnow()
    )


@router.post("/batch", response_model=BatchPredictionResponse)
async def predict_batch(
    data: BatchPredictionRequest,
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
    background_tasks: BackgroundTasks,
):
    """
    Predict dropout risk for multiple students.
    Processes in batch for efficiency.
    """
    predictions = []
    errors = []
    
    # Get all students
    result = await db.execute(
        select(Student).where(
            Student.id.in_(data.student_ids),
            Student.tenant_id == tenant.id,
            Student.is_deleted == False
        )
    )
    students = {s.id: s for s in result.scalars().all()}
    
    predictor = RiskPredictor(tenant_id=tenant.id)
    
    for student_id in data.student_ids:
        if student_id not in students:
            errors.append({
                "student_id": student_id,
                "error": "Student not found"
            })
            continue
        
        try:
            student = students[student_id]
            prediction = await predictor.predict(student, db)
            
            # Update student
            student.current_risk_score = prediction["risk_score"]
            student.current_risk_level = RiskLevel(prediction["risk_level"])
            student.risk_updated_at = datetime.utcnow()
            student.requires_attention = prediction["risk_level"] in ["high", "critical"]
            
            predictions.append(PredictionResponse(
                student_id=student.id,
                risk_score=prediction["risk_score"],
                risk_level=RiskLevel(prediction["risk_level"]),
                confidence=prediction.get("confidence"),
                top_factors=[
                    FactorContribution(**f) for f in prediction["top_factors"]
                ],
                explanation=prediction["explanation"],
                model_version=prediction.get("model_version", "1.0.0"),
                predicted_at=datetime.utcnow()
            ))
        except Exception as e:
            errors.append({
                "student_id": student_id,
                "error": str(e)
            })
    
    await db.commit()
    
    # Audit log
    background_tasks.add_task(
        create_audit_log,
        db=db,
        action=AuditAction.BULK_PREDICTION,
        user_id=current_user.id,
        tenant_id=tenant.id,
        resource_type="students",
        resource_id=None,
        description=f"Batch prediction for {len(data.student_ids)} students",
        details={"successful": len(predictions), "failed": len(errors)}
    )
    
    return BatchPredictionResponse(
        predictions=predictions,
        total=len(data.student_ids),
        successful=len(predictions),
        failed=len(errors),
        errors=errors
    )


@router.get("/insights/global", response_model=GlobalInsightsResponse)
async def get_global_insights(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """
    Get global insights about dropout risk drivers.
    Shows what factors contribute most across all students.
    """
    predictor = RiskPredictor(tenant_id=tenant.id)
    insights = await predictor.get_global_insights(db)
    
    return GlobalInsightsResponse(
        top_risk_drivers=insights.get("top_drivers", []),
        department_insights=insights.get("by_department", {}),
        semester_insights=insights.get("by_semester", {}),
        model_performance=insights.get("model_metrics", {})
    )


@router.get("/model/info")
async def get_model_info(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get information about the currently deployed model."""
    result = await db.execute(
        select(ModelVersion).where(
            ModelVersion.status == ModelStatus.DEPLOYED
        ).order_by(ModelVersion.deployed_at.desc()).limit(1)
    )
    model_version = result.scalar_one_or_none()
    
    if not model_version:
        return {
            "model_available": False,
            "message": "No model currently deployed"
        }
    
    return {
        "model_available": True,
        "version": model_version.version,
        "deployed_at": model_version.deployed_at,
        "accuracy": model_version.accuracy,
        "auc_roc": model_version.auc_roc,
        "fairness_metrics": model_version.fairness_metrics,
        "bias_detected": model_version.bias_detected,
        "feature_importance": model_version.feature_importance
    }
