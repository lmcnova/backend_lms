from pydantic import BaseModel, Field
from typing import Optional, Literal


class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: int = Field(0, ge=0)
    is_preview: bool = False
    order_index: Optional[int] = Field(None, ge=1)
    source_type: Literal["url", "upload"] = "url"
    storage_key: Optional[str] = None
    thumbnail_storage_key: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    original_filename: Optional[str] = None


class VideoCreate(VideoBase):
    pass


class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = Field(None, ge=0)
    is_preview: Optional[bool] = None
    order_index: Optional[int] = Field(None, ge=1)
    source_type: Optional[Literal["url", "upload"]] = None
    storage_key: Optional[str] = None
    thumbnail_storage_key: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    original_filename: Optional[str] = None


class VideoResponse(VideoBase):
    uuid_id: str
    course_uuid: str
    topic_uuid: str

    class Config:
        from_attributes = True
