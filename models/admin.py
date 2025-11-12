from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from uuid import uuid4

class AdminBase(BaseModel):
    college_name: str = Field(..., min_length=1, max_length=200)
    email_id: EmailStr
    total_student_allow_count: int = Field(..., ge=0)
    # Persisted role for admin documents
    role: Literal["admin"] = "admin"

class AdminCreate(AdminBase):
    password: str = Field(..., min_length=6)

class AdminUpdate(BaseModel):
    college_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email_id: Optional[EmailStr] = None
    total_student_allow_count: Optional[int] = Field(None, ge=0)
    password: Optional[str] = Field(None, min_length=6)
    # Role updates are not allowed via API

class AdminResponse(AdminBase):
    uuid_id: str

    class Config:
        from_attributes = True

class AdminInDB(AdminBase):
    uuid_id: str
    hashed_password: str
