from pydantic import BaseModel, Field
from typing import Literal, Optional


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentCreate(CommentBase):
    parent_type: Literal["topic", "video"]
    parent_uuid: str


class CommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000)
    status: Optional[Literal["visible", "hidden", "deleted"]] = None


class CommentResponse(CommentBase):
    uuid_id: str
    parent_type: str
    parent_uuid: str
    course_uuid: str
    author_role: str
    author_uuid: str
    status: str

    class Config:
        from_attributes = True

