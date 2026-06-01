from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.ai import categorize_complaint
from backend.database import Base, SessionLocal, engine
from backend.models import Complaint

app = FastAPI(title="AI Complaint Categorizer Backend")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ComplaintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1)


class ComplaintResponse(BaseModel):
    id: int
    name: str
    text: str
    category: str | None
    priority: str | None
    summary: str | None
    status: str


class ResolveComplaintResponse(BaseModel):
    id: int
    status: str


def _serialize_complaint(complaint: Complaint) -> ComplaintResponse:
    return ComplaintResponse(
        id=complaint.id,
        name=complaint.name,
        text=complaint.text,
        category=complaint.category,
        priority=complaint.priority,
        summary=complaint.summary,
        status=complaint.status,
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
        status="pending",
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return _serialize_complaint(complaint)


@app.get("/api/complaints", response_model=list[ComplaintResponse])
def list_complaints(db: Session = Depends(get_db)) -> list[ComplaintResponse]:
    complaints = db.query(Complaint).order_by(Complaint.id.desc()).all()
    return [_serialize_complaint(complaint) for complaint in complaints]


@app.patch("/api/complaints/{complaint_id}/resolve", response_model=ResolveComplaintResponse)
def resolve_complaint(complaint_id: int, db: Session = Depends(get_db)) -> ResolveComplaintResponse:
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = "resolved"
    db.commit()
    db.refresh(complaint)

    return ResolveComplaintResponse(id=complaint.id, status=complaint.status)
