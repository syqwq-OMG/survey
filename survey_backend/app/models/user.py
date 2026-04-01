from pydantic import BaseModel, Field
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, description="密码")


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str
