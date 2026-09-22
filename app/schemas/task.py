from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    completed: bool = False
    user_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)
