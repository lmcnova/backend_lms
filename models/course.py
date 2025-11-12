from pydantic import BaseModel, Field
from typing import Optional, List


class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    category: str = Field(..., min_length=1, max_length=50)
    level: str = Field(..., pattern=r"^(beginner|intermediate|advanced)$")
    description: Optional[str] = None
    tags: List[str] = []
    thumbnail_url: Optional[str] = None
    thumbnail_storage_key: Optional[str] = None
    intro_video_url: Optional[str] = None
    intro_video_storage_key: Optional[str] = None
    instructor_uuid: str
    co_instructor_uuids: List[str] = []
    departments: List[str] = Field(default=[], description="List of departments this course is available for")
    auto_assign: bool = Field(default=False, description="Auto-assign course to students when they join matching departments")


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    level: Optional[str] = Field(None, pattern=r"^(beginner|intermediate|advanced)$")
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    thumbnail_storage_key: Optional[str] = None
    intro_video_url: Optional[str] = None
    intro_video_storage_key: Optional[str] = None
    instructor_uuid: Optional[str] = None
    co_instructor_uuids: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    auto_assign: Optional[bool] = None


class CourseResponse(CourseBase):
    uuid_id: str
    slug: str
    total_topics: int
    total_videos: int
    total_comments: int

    class Config:
        from_attributes = True

