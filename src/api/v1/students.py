"""
Student management endpoints.
CRUD operations with tenant isolation and RBAC.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import CurrentUser, CurrentTenant, DBSession, MentorUser, require_permission
from src.models.student import Student, StudentRiskScore, RiskLevel, StudentStatus
from src.models.user import User


router = APIRouter()


# Schemas
class StudentBase(BaseModel):
    """Base student schema."""
    student_id: str = Field(..., description="Institution's student ID")
    first_name: str
    last_name: str
    email: Optional[str] = None
    department: str
    program: Optional[str] = None
    semester: int = 1
    gender: Optional[str] = None
    socioeconomic_status: Optional[str] = None
    region: Optional[str] = None


class StudentCreate(StudentBase):
    """Create student schema."""
    enrollment_date: datetime


class StudentUpdate(BaseModel):
    """Update student schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[int] = None
    status: Optional[StudentStatus] = None
    mentor_id: Optional[str] = None
    
    # Engagement metrics (typically updated via batch)
    gpa: Optional[float] = None
    attendance_rate: Optional[float] = None
    assignment_submission_rate: Optional[float] = None
    late_submissions: Optional[int] = None
    lms_login_frequency: Optional[int] = None
    forum_posts: Optional[int] = None
    resource_access_count: Optional[int] = None
    time_spent_hours: Optional[float] = None
    participation_score: Optional[float] = None
    exam_scores: Optional[float] = None


class StudentResponse(BaseModel):
    """Student response schema."""
    id: str
    student_id: str
    first_name: str
    last_name: str
    email: Optional[str]
    department: str
    program: Optional[str]
    semester: int
    status: StudentStatus
    current_risk_level: Optional[RiskLevel]
    current_risk_score: Optional[float]
    requires_attention: bool
    intervention_active: bool
    mentor_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class StudentDetailResponse(StudentResponse):
    """Detailed student response with metrics."""
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
    """Paginated student list."""
    items: List[StudentResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RiskScoreResponse(BaseModel):
    """Risk score history response."""
    id: str
    risk_score: float
    risk_level: RiskLevel
    top_factors: dict
    explanation_text: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("", response_model=StudentListResponse)
async def list_students(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department: Optional[str] = None,
    risk_level: Optional[RiskLevel] = None,
    status: Optional[StudentStatus] = None,
    search: Optional[str] = None,
    mentor_id: Optional[str] = None,
    requires_attention: Optional[bool] = None,
):
    """
    List students with filtering and pagination.
    Respects user permissions (mentor sees only assigned).
    """
    # Base query with tenant isolation
    query = select(Student).where(
        Student.tenant_id == tenant.id,
        Student.is_deleted == False
    )
    
    # Role-based filtering
    if current_user.role.value in ["mentor", "counselor"]:
        # Only show assigned students
        query = query.where(Student.mentor_id == current_user.id)
    elif current_user.role.value == "department_head" and current_user.department:
        # Only show department students
        query = query.where(Student.department == current_user.department)
    
    # Apply filters
    if department:
        query = query.where(Student.department == department)
    if risk_level:
        query = query.where(Student.current_risk_level == risk_level)
    if status:
        query = query.where(Student.status == status)
    if mentor_id:
        query = query.where(Student.mentor_id == mentor_id)
    if requires_attention is not None:
        query = query.where(Student.requires_attention == requires_attention)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Student.first_name.ilike(search_term)) |
            (Student.last_name.ilike(search_term)) |
            (Student.student_id.ilike(search_term))
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Student.created_at.desc())
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    return StudentListResponse(
        items=[StudentResponse.model_validate(s) for s in students],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{student_id}", response_model=StudentDetailResponse)
async def get_student(
    student_id: str,
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get student details by ID."""
    result = await db.execute(
        select(Student).where(
            Student.id == student_id,
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
    
    # Check access
    if current_user.role.value in ["mentor", "counselor"]:
        if student.mentor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this student"
            )
    
    return StudentDetailResponse.model_validate(student)


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Create a new student."""
    # Check permission
    if not current_user.has_permission("manage_students"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # Check for duplicate student_id
    existing = await db.execute(
        select(Student).where(
            Student.tenant_id == tenant.id,
            Student.student_id == data.student_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID already exists"
        )
    
    student = Student(
        tenant_id=tenant.id,
        **data.model_dump()
    )
    
    db.add(student)
    await db.commit()
    await db.refresh(student)
    
    return StudentResponse.model_validate(student)


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: str,
    data: StudentUpdate,
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Update student details."""
    result = await db.execute(
        select(Student).where(
            Student.id == student_id,
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
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    
    await db.commit()
    await db.refresh(student)
    
    return StudentResponse.model_validate(student)


@router.get("/{student_id}/risk-history", response_model=List[RiskScoreResponse])
async def get_risk_history(
    student_id: str,
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
    limit: int = Query(10, ge=1, le=50),
):
    """Get student's risk score history."""
    result = await db.execute(
        select(StudentRiskScore).where(
            StudentRiskScore.student_id == student_id,
            StudentRiskScore.tenant_id == tenant.id
        ).order_by(StudentRiskScore.created_at.desc()).limit(limit)
    )
    scores = result.scalars().all()
    
    return [RiskScoreResponse.model_validate(s) for s in scores]


@router.get("/stats/summary")
async def get_students_summary(
    db: DBSession,
    current_user: CurrentUser,
    tenant: CurrentTenant,
):
    """Get summary statistics for students."""
    # Base query
    base_query = select(Student).where(
        Student.tenant_id == tenant.id,
        Student.is_deleted == False
    )
    
    # Total students
    total = await db.scalar(
        select(func.count()).select_from(base_query.subquery())
    )
    
    # By risk level
    risk_counts = await db.execute(
        select(
            Student.current_risk_level,
            func.count(Student.id)
        ).where(
            Student.tenant_id == tenant.id,
            Student.is_deleted == False,
            Student.current_risk_level.isnot(None)
        ).group_by(Student.current_risk_level)
    )
    
    risk_distribution = {
        row[0].value if row[0] else "unknown": row[1]
        for row in risk_counts.all()
    }
    
    # Requires attention
    attention_count = await db.scalar(
        select(func.count()).where(
            Student.tenant_id == tenant.id,
            Student.is_deleted == False,
            Student.requires_attention == True
        )
    )
    
    # By department
    dept_counts = await db.execute(
        select(
            Student.department,
            func.count(Student.id)
        ).where(
            Student.tenant_id == tenant.id,
            Student.is_deleted == False
        ).group_by(Student.department)
    )
    
    by_department = {row[0]: row[1] for row in dept_counts.all()}
    
    return {
        "total_students": total,
        "risk_distribution": risk_distribution,
        "requires_attention": attention_count,
        "by_department": by_department
    }
