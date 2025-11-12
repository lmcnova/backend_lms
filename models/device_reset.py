from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class DeviceResetRequestCreate(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class DeviceResetRequestResponse(BaseModel):
    request_id: str
    student_uuid: str
    status: Literal["pending", "approved", "rejected"]
    reason: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by_uuid: Optional[str] = None
    resolved_by_role: Optional[str] = None

