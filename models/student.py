from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from uuid import uuid4

class StudentBase(BaseModel):
    student_name: str = Field(..., min_length=1, max_length=200)
    department: str = Field(..., min_length=1, max_length=100)
    email_id: EmailStr
    sub_department: Optional[str] = Field(None, max_length=100)
    admin_uuid_id: str = Field(..., description="Foreign key reference to admin UUID")
    avatar_url: Optional[str] = None
    avatar_file_key: Optional[str] = None  # S3 storage key
    # Persisted role for student documents
    role: Literal["student"] = "student"

class StudentCreate(StudentBase):
    password: str = Field(..., min_length=6)

class StudentUpdate(BaseModel):
    student_name: Optional[str] = Field(None, min_length=1, max_length=200)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    email_id: Optional[EmailStr] = None
    sub_department: Optional[str] = Field(None, max_length=100)
    admin_uuid_id: Optional[str] = Field(None, description="Foreign key reference to admin UUID")
    avatar_url: Optional[str] = None
    avatar_file_key: Optional[str] = None  # S3 storage key
    password: Optional[str] = Field(None, min_length=6)
    # Role updates are not allowed via API

class StudentResponse(StudentBase):
    uuid_id: str

    class Config:
        from_attributes = True

class StudentInDB(StudentBase):
    uuid_id: str
    hashed_password: str
