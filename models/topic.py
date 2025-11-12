from pydantic import BaseModel, Field
from typing import Optional


class TopicBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=1)


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=1)


class TopicResponse(TopicBase):
    uuid_id: str
    course_uuid: str

    class Config:
        from_attributes = True

