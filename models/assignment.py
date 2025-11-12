from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class AssignRequest(BaseModel):
    course_uuid: str
    student_uuid: Optional[str] = None
    student_uuids: Optional[List[str]] = None


class AssignmentResponse(BaseModel):
    uuid_id: str
    student_uuid: str
    course_uuid: str
    assigned_by_role: Literal["admin", "teacher", "student", "system"]
    assigned_by_uuid: str
    status: Literal["active", "completed", "revoked"]
    assigned_at: datetime

    class Config:
        from_attributes = True

