from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)
