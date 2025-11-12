from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SessionCreate(BaseModel):
    user_uuid: str
    role: str
    device_name: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class SessionInDB(BaseModel):
    session_id: str
    user_uuid: str
    role: str
    device_name: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_used_at: datetime
    revoked: bool = False


class SessionResponse(BaseModel):
    session_id: str
    device_name: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_used_at: datetime

    class Config:
        from_attributes = True

