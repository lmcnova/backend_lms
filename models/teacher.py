from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


class TeacherBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email_id: EmailStr
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_file_key: Optional[str] = None  # S3 storage key
    skills: list[str] = []
    social_links: Optional[dict] = None
    role: Literal["teacher"] = "teacher"


class TeacherCreate(TeacherBase):
    password: str = Field(..., min_length=6)


class TeacherUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    email_id: Optional[EmailStr] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_file_key: Optional[str] = None  # S3 storage key
    skills: Optional[list[str]] = None
    social_links: Optional[dict] = None
    password: Optional[str] = Field(None, min_length=6)


class TeacherResponse(TeacherBase):
    uuid_id: str

    class Config:
        from_attributes = True


class TeacherInDB(TeacherBase):
    uuid_id: str
    hashed_password: str

