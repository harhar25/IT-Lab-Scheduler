from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LabBase(BaseModel):
    name: str
    description: Optional[str] = None
    capacity: int
    equipment: Optional[str] = None

class LabCreate(LabBase):
    pass

class LabUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    equipment: Optional[str] = None
    is_active: Optional[bool] = None

class Lab(LabBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True