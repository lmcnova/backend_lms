from pydantic import BaseModel, Field
from typing import Optional


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    admin_uuid_id: str = Field(..., description="Foreign key reference to admin UUID")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    admin_uuid_id: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    uuid_id: str

    class Config:
        from_attributes = True


class DepartmentInDB(DepartmentBase):
    uuid_id: str
