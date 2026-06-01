from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.ai import categorize_complaint
from backend.database import Base, SessionLocal, engine
from backend.models import Complaint
from backend.schemas import (
    ComplaintAnalyticsResponse,
    ComplaintCategory,
    ComplaintCreate,
    ComplaintPriority,
    ComplaintResponse,
    ComplaintStatus,
    ResolveComplaintResponse,
)

app = FastAPI(title="AI Complaint Categorizer Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _serialize_complaint(complaint: Complaint) -> ComplaintResponse:
    category = (
        complaint.category if complaint.category in {item.value for item in ComplaintCategory} else None
    )
    priority = (
        complaint.priority if complaint.priority in {item.value for item in ComplaintPriority} else None
    )
    status = (
        ComplaintStatus.RESOLVED
        if complaint.status == ComplaintStatus.RESOLVED.value
        else ComplaintStatus.PENDING
    )
    return ComplaintResponse(
        id=complaint.id,
        name=complaint.name,
        text=complaint.text,
        category=category,
        priority=priority,
        summary=complaint.summary,
        status=status,
    )


@app.post("/api/complaints", response_model=ComplaintResponse)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)) -> ComplaintResponse:
    ai_result = categorize_complaint(payload.text)

    complaint = Complaint(
        name=payload.name,
        text=payload.text,
        category=ai_result.get("category"),
        priority=ai_result.get("priority"),
        summary=ai_result.get("summary"),
        status=ComplaintStatus.PENDING.value,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return _serialize_complaint(complaint)


@app.get("/api/complaints", response_model=list[ComplaintResponse])
def list_complaints(
    category: ComplaintCategory | None = None,
    status: ComplaintStatus | None = None,
    priority: ComplaintPriority | None = None,
    db: Session = Depends(get_db),
) -> list[ComplaintResponse]:
    query = db.query(Complaint)
    if category is not None:
        query = query.filter(Complaint.category == category.value)
    if status is not None:
        query = query.filter(Complaint.status == status.value)
    if priority is not None:
        query = query.filter(Complaint.priority == priority.value)
    complaints = query.order_by(Complaint.id.desc()).all()
    return [_serialize_complaint(complaint) for complaint in complaints]


@app.patch("/api/complaints/{complaint_id}/resolve", response_model=ResolveComplaintResponse)
def resolve_complaint(complaint_id: int, db: Session = Depends(get_db)) -> ResolveComplaintResponse:
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = ComplaintStatus.RESOLVED.value
    db.commit()
    db.refresh(complaint)

    return ResolveComplaintResponse(id=complaint.id, status=ComplaintStatus.RESOLVED)


@app.get("/api/analytics", response_model=ComplaintAnalyticsResponse)
def complaint_analytics(db: Session = Depends(get_db)) -> ComplaintAnalyticsResponse:
    total = db.query(func.count(Complaint.id)).scalar() or 0
    high_priority = db.query(func.count(Complaint.id)).filter(Complaint.priority == "High").scalar() or 0
    resolved = (
        db.query(func.count(Complaint.id))
        .filter(Complaint.status == ComplaintStatus.RESOLVED.value)
        .scalar()
        or 0
    )
    return ComplaintAnalyticsResponse(total=total, high_priority=high_priority, resolved=resolved)
