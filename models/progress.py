from pydantic import BaseModel, Field
from typing import Optional


class ProgressUpdate(BaseModel):
    last_position_sec: int = Field(..., ge=0)
    delta_seconds_watched: int = Field(0, ge=0)
    completed: Optional[bool] = None


class VideoProgressResponse(BaseModel):
    video_uuid: str
    course_uuid: str
    topic_uuid: str
    seconds_watched: int
    last_position_sec: int
    completed: bool


class CourseProgressResponse(BaseModel):
    course_uuid: str
    total_videos: int
    completed_videos: int
    progress_percent: float
    learning_seconds: int
    learning_hours: float
