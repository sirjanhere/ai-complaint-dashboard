from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ComplaintStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"


class ComplaintCategory(str, Enum):
    WIFI = "WiFi"
    HOSTEL = "Hostel"
    ELECTRICITY = "Electricity"
    CLASSROOM = "Classroom"
    OTHER = "Other"


class ComplaintPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ComplaintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1)

    @field_validator("name", "text")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be empty")
        return normalized


class ComplaintResponse(BaseModel):
    id: int
    name: str
    text: str
    category: ComplaintCategory | None
    priority: ComplaintPriority | None
    summary: str | None
    status: ComplaintStatus


class ResolveComplaintResponse(BaseModel):
    id: int
    status: ComplaintStatus


class ComplaintAnalyticsResponse(BaseModel):
    total: int
    high_priority: int
    resolved: int
