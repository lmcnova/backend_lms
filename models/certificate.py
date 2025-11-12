from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CertificateCreate(BaseModel):
    course_uuid: str
    student_uuid: str


class CertificateUpdate(BaseModel):
    url: Optional[str] = None
    certificate_file_key: Optional[str] = None
    revoked: Optional[bool] = None
    notes: Optional[str] = None


class CertificateResponse(BaseModel):
    certificate_id: str
    course_uuid: str
    student_uuid: str
    student_name: Optional[str] = None
    course_title: Optional[str] = None
    issued_at: datetime
    code: str
    url: Optional[str] = None
    certificate_file_key: Optional[str] = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    notes: Optional[str] = None
    completion_percentage: Optional[float] = None

    class Config:
        from_attributes = True


class EligibilityResponse(BaseModel):
    eligible: bool
    reason: Optional[str] = None
    certificate: Optional[CertificateResponse] = None
    completion_percentage: Optional[float] = None

