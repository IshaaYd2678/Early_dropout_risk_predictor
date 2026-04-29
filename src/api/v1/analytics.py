"""
Analytics endpoints for dashboards and reports.
Provides aggregated insights for different user roles.
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import CurrentUser, CurrentTenant, DBSession
from src.models.student import Student, StudentRiskScore, RiskLevel, StudentStatus
from src.models.intervention import Intervention, InterventionOutcome


router = APIRouter()


class DashboardMetrics(BaseModel):
    """Overview dashboard metrics."""
    total_students: int
    active_students: int
    at_risk_students: int
    critical_students: int
    dropout_rate: float
    avg_risk_score: Optional[float]
    interventions_active: int
    interventions_success_rate: float


class RiskTrendPoint(BaseModel):
    """Risk trend data point."""
    date: str
    low: int
    medium: int
    high: int
    critical: int


class DepartmentMetrics(BaseModel):
    """Department-level metrics."""
    department: str
    total_students: int
    at_risk_count: int
    at_risk_percentage: float
    avg_risk_score: Optional[float]
    interventions_count: int


class FairnessMetrics(BaseModel):
    """Fairness metrics across demographics."""
    attribute: str
    groups: List[dict]
    parity_difference: float
    equal_opportunity_difference: float
    bias_detected: bool


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get main dashboard metrics."""
    base_query = and_(
        Student.tenant_id == tenant.id,
        Student.is_deleted == False
    )
    
    # Total and active students
    total = await db.scalar(select(func.count()).where(base_query))
    active = await db.scalar(
        select(func.count()).where(
            base_query,
            Student.status == StudentStatus.ENROLLED
        )
    )
    
    # At risk counts
    at_risk = await db.scalar(
        select(func.count()).where(
            base_query,
            Student.current_risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        )
    )
    critical = await db.scalar(
        select(func.count()).where(
            base_query,
            Student.current_risk_level == RiskLevel.CRITICAL
        )
    )
    
    # Dropout rate
    dropped = await db.scalar(
        select(func.count()).where(
            base_query,
            Student.status == StudentStatus.DROPPED_OUT
        )
    )
    dropout_rate = (dropped / total * 100) if total > 0 else 0
    
    # Average risk score
    avg_risk = await db.scalar(
        select(func.avg(Student.current_risk_score)).where(
            base_query,
            Student.current_risk_score.isnot(None)
        )
    )
    
    # Interventions
    interventions_active = await db.scalar(
        select(func.count()).where(
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False,
            Intervention.status.in_(["approved", "scheduled", "in_progress"])
        )
    )
    
    # Intervention success rate
    successful = await db.scalar(
        select(func.count()).where(
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False,
            Intervention.outcome.in_([InterventionOutcome.RISK_REDUCED, InterventionOutcome.STUDENT_RETAINED])
        )
    )
    completed = await db.scalar(
        select(func.count()).where(
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False,
            Intervention.outcome != InterventionOutcome.PENDING
        )
    )
    success_rate = (successful / completed * 100) if completed > 0 else 0
    
    return DashboardMetrics(
        total_students=total,
        active_students=active,
        at_risk_students=at_risk,
        critical_students=critical,
        dropout_rate=round(dropout_rate, 2),
        avg_risk_score=round(avg_risk, 4) if avg_risk else None,
        interventions_active=interventions_active,
        interventions_success_rate=round(success_rate, 2)
    )


@router.get("/risk-trends", response_model=List[RiskTrendPoint])
async def get_risk_trends(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
    days: int = Query(30, ge=7, le=365),
):
    """Get risk level trends over time."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily risk counts
    result = await db.execute(
        select(
            func.date(StudentRiskScore.created_at).label('date'),
            StudentRiskScore.risk_level,
            func.count(StudentRiskScore.id)
        ).where(
            StudentRiskScore.tenant_id == tenant.id,
            StudentRiskScore.created_at >= start_date
        ).group_by(
            func.date(StudentRiskScore.created_at),
            StudentRiskScore.risk_level
        ).order_by('date')
    )
    
    # Organize by date
    trends = {}
    for row in result.all():
        date_str = str(row[0])
        if date_str not in trends:
            trends[date_str] = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        trends[date_str][row[1].value] = row[2]
    
    return [
        RiskTrendPoint(date=date, **counts)
        for date, counts in sorted(trends.items())
    ]


@router.get("/departments", response_model=List[DepartmentMetrics])
async def get_department_metrics(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get metrics broken down by department."""
    result = await db.execute(
        select(
            Student.department,
            func.count(Student.id).label('total'),
            func.sum(
                case(
                    (Student.current_risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]), 1),
                    else_=0
                )
            ).label('at_risk'),
            func.avg(Student.current_risk_score).label('avg_risk')
        ).where(
            Student.tenant_id == tenant.id,
            Student.is_deleted == False,
            Student.status == StudentStatus.ENROLLED
        ).group_by(Student.department)
    )
    
    departments = []
    for row in result.all():
        # Get intervention count for department
        intervention_count = await db.scalar(
            select(func.count()).select_from(Intervention).join(Student).where(
                Student.department == row[0],
                Student.tenant_id == tenant.id,
                Intervention.is_deleted == False
            )
        )
        
        total = row[1] or 0
        at_risk = row[2] or 0
        
        departments.append(DepartmentMetrics(
            department=row[0],
            total_students=total,
            at_risk_count=at_risk,
            at_risk_percentage=round((at_risk / total * 100) if total > 0 else 0, 2),
            avg_risk_score=round(row[3], 4) if row[3] else None,
            interventions_count=intervention_count or 0
        ))
    
    return sorted(departments, key=lambda x: x.at_risk_percentage, reverse=True)


@router.get("/fairness", response_model=List[FairnessMetrics])
async def get_fairness_metrics(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get fairness metrics across demographic groups."""
    metrics = []
    
    # Analyze by gender
    gender_result = await db.execute(
        select(
            Student.gender,
            func.count(Student.id).label('total'),
            func.avg(Student.current_risk_score).label('avg_risk'),
            func.sum(
                case(
                    (Student.current_risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]), 1),
                    else_=0
                )
            ).label('flagged')
        ).where(
            Student.tenant_id == tenant.id,
            Student.is_deleted == False,
            Student.gender.isnot(None)
        ).group_by(Student.gender)
    )
    
    gender_groups = []
    flagged_rates = []
    for row in gender_result.all():
        total = row[1] or 1
        flagged = row[3] or 0
        flagged_rate = flagged / total
        flagged_rates.append(flagged_rate)
        gender_groups.append({
            "group": row[0],
            "count": total,
            "avg_risk": round(row[2], 4) if row[2] else None,
            "flagged_rate": round(flagged_rate, 4)
        })
    
    parity_diff = max(flagged_rates) - min(flagged_rates) if flagged_rates else 0
    
    metrics.append(FairnessMetrics(
        attribute="gender",
        groups=gender_groups,
        parity_difference=round(parity_diff, 4),
        equal_opportunity_difference=round(parity_diff, 4),  # Simplified
        bias_detected=parity_diff > 0.1
    ))
    
    # Analyze by socioeconomic status
    ses_result = await db.execute(
        select(
            Student.socioeconomic_status,
            func.count(Student.id).label('total'),
            func.avg(Student.current_risk_score).label('avg_risk'),
            func.sum(
                case(
                    (Student.current_risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]), 1),
                    else_=0
                )
            ).label('flagged')
        ).where(
            Student.tenant_id == tenant.id,
            Student.is_deleted == False,
            Student.socioeconomic_status.isnot(None)
        ).group_by(Student.socioeconomic_status)
    )
    
    ses_groups = []
    ses_rates = []
    for row in ses_result.all():
        total = row[1] or 1
        flagged = row[3] or 0
        flagged_rate = flagged / total
        ses_rates.append(flagged_rate)
        ses_groups.append({
            "group": row[0],
            "count": total,
            "avg_risk": round(row[2], 4) if row[2] else None,
            "flagged_rate": round(flagged_rate, 4)
        })
    
    ses_parity = max(ses_rates) - min(ses_rates) if ses_rates else 0
    
    metrics.append(FairnessMetrics(
        attribute="socioeconomic_status",
        groups=ses_groups,
        parity_difference=round(ses_parity, 4),
        equal_opportunity_difference=round(ses_parity, 4),
        bias_detected=ses_parity > 0.1
    ))
    
    return metrics


@router.get("/intervention-effectiveness")
async def get_intervention_effectiveness(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get intervention effectiveness analysis."""
    result = await db.execute(
        select(
            Intervention.intervention_type,
            func.count(Intervention.id).label('total'),
            func.sum(
                case(
                    (Intervention.outcome.in_([InterventionOutcome.RISK_REDUCED, InterventionOutcome.STUDENT_RETAINED]), 1),
                    else_=0
                )
            ).label('successful'),
            func.avg(Intervention.risk_score_before - Intervention.risk_score_after).label('avg_reduction')
        ).where(
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False,
            Intervention.outcome != InterventionOutcome.PENDING
        ).group_by(Intervention.intervention_type)
    )
    
    effectiveness = []
    for row in result.all():
        total = row[1] or 1
        successful = row[2] or 0
        effectiveness.append({
            "intervention_type": row[0].value,
            "total_count": total,
            "success_count": successful,
            "success_rate": round(successful / total * 100, 2),
            "avg_risk_reduction": round(row[3], 4) if row[3] else None
        })
    
    return sorted(effectiveness, key=lambda x: x["success_rate"], reverse=True)
