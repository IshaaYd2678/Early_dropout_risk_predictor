"""
Intervention management endpoints.
Full workflow from recommendation to outcome tracking.
"""
from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import CurrentUser, CurrentTenant, DBSession, MentorUser
from src.models.intervention import (
    Intervention, InterventionFollowUp,
    InterventionType, InterventionStatus, InterventionOutcome, InterventionPriority
)
from src.models.student import Student
from src.services.audit import create_audit_log
from src.models.audit import AuditAction


router = APIRouter()


# Schemas
class InterventionCreate(BaseModel):
    """Create intervention schema."""
    student_id: str
    intervention_type: InterventionType
    title: str
    description: Optional[str] = None
    priority: InterventionPriority = InterventionPriority.MEDIUM
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None


class InterventionUpdate(BaseModel):
    """Update intervention schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[InterventionPriority] = None
    status: Optional[InterventionStatus] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None


class OutcomeUpdate(BaseModel):
    """Update intervention outcome."""
    outcome: InterventionOutcome
    outcome_notes: Optional[str] = None
    risk_score_after: Optional[float] = None


class FollowUpCreate(BaseModel):
    """Create follow-up record."""
    notes: str
    outcome_update: Optional[str] = None
    next_followup_date: Optional[date] = None


class InterventionResponse(BaseModel):
    """Intervention response schema."""
    id: str
    student_id: str
    intervention_type: InterventionType
    title: str
    description: Optional[str]
    status: InterventionStatus
    priority: InterventionPriority
    outcome: InterventionOutcome
    scheduled_date: Optional[date]
    risk_score_before: Optional[float]
    risk_score_after: Optional[float]
    created_by: str
    assigned_to: Optional[str]
    ai_recommended: bool
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class InterventionDetailResponse(InterventionResponse):
    """Detailed intervention with follow-ups."""
    student_name: Optional[str] = None
    follow_ups: List[dict] = []
    risk_change: Optional[float] = None


class InterventionListResponse(BaseModel):
    """Paginated intervention list."""
    items: List[InterventionResponse]
    total: int
    page: int
    page_size: int


class InterventionStatsResponse(BaseModel):
    """Intervention statistics."""
    total_interventions: int
    by_type: dict
    by_status: dict
    by_outcome: dict
    success_rate: float
    avg_risk_reduction: Optional[float]


@router.get("", response_model=InterventionListResponse)
async def list_interventions(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[str] = None,
    intervention_type: Optional[InterventionType] = None,
    status: Optional[InterventionStatus] = None,
    outcome: Optional[InterventionOutcome] = None,
    priority: Optional[InterventionPriority] = None,
    assigned_to_me: bool = False,
):
    """List interventions with filtering."""
    query = select(Intervention).where(
        Intervention.tenant_id == tenant.id,
        Intervention.is_deleted == False
    )
    
    # Filters
    if student_id:
        query = query.where(Intervention.student_id == student_id)
    if intervention_type:
        query = query.where(Intervention.intervention_type == intervention_type)
    if status:
        query = query.where(Intervention.status == status)
    if outcome:
        query = query.where(Intervention.outcome == outcome)
    if priority:
        query = query.where(Intervention.priority == priority)
    if assigned_to_me:
        query = query.where(Intervention.assigned_to == current_user.id)
    
    # Count
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Intervention.created_at.desc())
    
    result = await db.execute(query)
    interventions = result.scalars().all()
    
    return InterventionListResponse(
        items=[InterventionResponse.model_validate(i) for i in interventions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{intervention_id}", response_model=InterventionDetailResponse)
async def get_intervention(
    intervention_id: str,
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get intervention details."""
    result = await db.execute(
        select(Intervention)
        .options(selectinload(Intervention.follow_ups))
        .options(selectinload(Intervention.student))
        .where(
            Intervention.id == intervention_id,
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False
        )
    )
    intervention = result.scalar_one_or_none()
    
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention not found"
        )
    
    response = InterventionDetailResponse.model_validate(intervention)
    response.student_name = intervention.student.full_name if intervention.student else None
    response.follow_ups = [
        {
            "id": f.id,
            "notes": f.notes,
            "created_at": f.created_at.isoformat()
        }
        for f in intervention.follow_ups
    ]
    response.risk_change = intervention.risk_change
    
    return response


@router.post("", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
async def create_intervention(
    data: InterventionCreate,
    db: DBSession,
    current_user: MentorUser,
    tenant: CurrentTenant,
    background_tasks: BackgroundTasks,
):
    """Create a new intervention."""
    # Verify student exists
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
    
    # Create intervention
    intervention = Intervention(
        tenant_id=tenant.id,
        student_id=data.student_id,
        intervention_type=data.intervention_type,
        title=data.title,
        description=data.description,
        priority=data.priority,
        status=InterventionStatus.PENDING_APPROVAL if data.priority == InterventionPriority.CRITICAL else InterventionStatus.APPROVED,
        scheduled_date=data.scheduled_date,
        scheduled_time=data.scheduled_time,
        duration_minutes=data.duration_minutes,
        location=data.location,
        created_by=current_user.id,
        assigned_to=data.assigned_to or current_user.id,
        risk_score_before=student.current_risk_score,
        risk_level_before=student.current_risk_level.value if student.current_risk_level else None,
    )
    
    db.add(intervention)
    
    # Update student flag
    student.intervention_active = True
    
    await db.commit()
    await db.refresh(intervention)
    
    # Audit log
    background_tasks.add_task(
        create_audit_log,
        db=db,
        action=AuditAction.INTERVENTION_CREATED,
        user_id=current_user.id,
        tenant_id=tenant.id,
        resource_type="intervention",
        resource_id=intervention.id,
        description=f"Intervention created for student {student.student_id}",
        details={"type": data.intervention_type.value, "priority": data.priority.value}
    )
    
    return InterventionResponse.model_validate(intervention)


@router.patch("/{intervention_id}", response_model=InterventionResponse)
async def update_intervention(
    intervention_id: str,
    data: InterventionUpdate,
    db: DBSession,
    current_user: MentorUser,
    tenant: CurrentTenant,
    background_tasks: BackgroundTasks,
):
    """Update intervention details."""
    result = await db.execute(
        select(Intervention).where(
            Intervention.id == intervention_id,
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False
        )
    )
    intervention = result.scalar_one_or_none()
    
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention not found"
        )
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    
    # Track status changes
    old_status = intervention.status
    
    for field, value in update_data.items():
        setattr(intervention, field, value)
    
    # Handle status transitions
    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == InterventionStatus.IN_PROGRESS and not intervention.started_at:
            intervention.started_at = datetime.utcnow()
        elif new_status == InterventionStatus.COMPLETED:
            intervention.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(intervention)
    
    # Audit log
    background_tasks.add_task(
        create_audit_log,
        db=db,
        action=AuditAction.INTERVENTION_UPDATED,
        user_id=current_user.id,
        tenant_id=tenant.id,
        resource_type="intervention",
        resource_id=intervention.id,
        description=f"Intervention updated",
        details=update_data
    )
    
    return InterventionResponse.model_validate(intervention)


@router.post("/{intervention_id}/outcome", response_model=InterventionResponse)
async def record_outcome(
    intervention_id: str,
    data: OutcomeUpdate,
    db: DBSession,
    current_user: MentorUser,
    tenant: CurrentTenant,
    background_tasks: BackgroundTasks,
):
    """Record intervention outcome."""
    result = await db.execute(
        select(Intervention)
        .options(selectinload(Intervention.student))
        .where(
            Intervention.id == intervention_id,
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False
        )
    )
    intervention = result.scalar_one_or_none()
    
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention not found"
        )
    
    # Update outcome
    intervention.outcome = data.outcome
    intervention.outcome_notes = data.outcome_notes
    intervention.outcome_recorded_at = datetime.utcnow()
    intervention.status = InterventionStatus.COMPLETED
    intervention.completed_at = datetime.utcnow()
    
    # Get current risk score if not provided
    if data.risk_score_after is not None:
        intervention.risk_score_after = data.risk_score_after
    elif intervention.student:
        intervention.risk_score_after = intervention.student.current_risk_score
    
    intervention.risk_level_after = intervention.student.current_risk_level.value if intervention.student and intervention.student.current_risk_level else None
    
    # Update student flags
    if intervention.student:
        # Check if there are other active interventions
        other_active = await db.scalar(
            select(func.count()).where(
                Intervention.student_id == intervention.student_id,
                Intervention.id != intervention.id,
                Intervention.status.in_([
                    InterventionStatus.APPROVED,
                    InterventionStatus.SCHEDULED,
                    InterventionStatus.IN_PROGRESS
                ])
            )
        )
        if other_active == 0:
            intervention.student.intervention_active = False
    
    await db.commit()
    await db.refresh(intervention)
    
    # Audit log
    background_tasks.add_task(
        create_audit_log,
        db=db,
        action=AuditAction.INTERVENTION_COMPLETED,
        user_id=current_user.id,
        tenant_id=tenant.id,
        resource_type="intervention",
        resource_id=intervention.id,
        description=f"Intervention outcome recorded: {data.outcome.value}",
        details={
            "outcome": data.outcome.value,
            "risk_before": intervention.risk_score_before,
            "risk_after": intervention.risk_score_after
        }
    )
    
    return InterventionResponse.model_validate(intervention)


@router.post("/{intervention_id}/followup")
async def add_followup(
    intervention_id: str,
    data: FollowUpCreate,
    db: DBSession,
    current_user: MentorUser,
    tenant: CurrentTenant,
):
    """Add a follow-up note to an intervention."""
    result = await db.execute(
        select(Intervention).where(
            Intervention.id == intervention_id,
            Intervention.tenant_id == tenant.id,
            Intervention.is_deleted == False
        )
    )
    intervention = result.scalar_one_or_none()
    
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention not found"
        )
    
    followup = InterventionFollowUp(
        intervention_id=intervention.id,
        created_by=current_user.id,
        notes=data.notes,
        outcome_update=data.outcome_update,
        next_followup_date=data.next_followup_date
    )
    
    db.add(followup)
    
    # Update intervention followup date
    if data.next_followup_date:
        intervention.requires_followup = True
        intervention.followup_date = data.next_followup_date
    
    await db.commit()
    
    return {"message": "Follow-up added successfully", "id": followup.id}


@router.get("/stats/summary", response_model=InterventionStatsResponse)
async def get_intervention_stats(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get intervention statistics."""
    base_query = and_(
        Intervention.tenant_id == tenant.id,
        Intervention.is_deleted == False
    )
    
    # Total
    total = await db.scalar(
        select(func.count()).where(base_query)
    )
    
    # By type
    type_counts = await db.execute(
        select(Intervention.intervention_type, func.count())
        .where(base_query)
        .group_by(Intervention.intervention_type)
    )
    by_type = {row[0].value: row[1] for row in type_counts.all()}
    
    # By status
    status_counts = await db.execute(
        select(Intervention.status, func.count())
        .where(base_query)
        .group_by(Intervention.status)
    )
    by_status = {row[0].value: row[1] for row in status_counts.all()}
    
    # By outcome
    outcome_counts = await db.execute(
        select(Intervention.outcome, func.count())
        .where(base_query)
        .group_by(Intervention.outcome)
    )
    by_outcome = {row[0].value: row[1] for row in outcome_counts.all()}
    
    # Success rate
    completed = by_outcome.get("risk_reduced", 0) + by_outcome.get("student_retained", 0)
    total_with_outcome = sum(v for k, v in by_outcome.items() if k != "pending")
    success_rate = (completed / total_with_outcome * 100) if total_with_outcome > 0 else 0
    
    # Average risk reduction
    avg_reduction = await db.scalar(
        select(func.avg(Intervention.risk_score_before - Intervention.risk_score_after))
        .where(
            base_query,
            Intervention.risk_score_before.isnot(None),
            Intervention.risk_score_after.isnot(None)
        )
    )
    
    return InterventionStatsResponse(
        total_interventions=total,
        by_type=by_type,
        by_status=by_status,
        by_outcome=by_outcome,
        success_rate=round(success_rate, 2),
        avg_risk_reduction=round(avg_reduction, 4) if avg_reduction else None
    )
