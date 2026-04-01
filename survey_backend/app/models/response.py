# app/models/response.py
from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime


class AnswerItem(BaseModel):
    q_id: str = Field(..., description="题目ID")
    value: Any = Field(..., description="用户填写的答案(字符串/数字/列表)")


class ResponseCreate(BaseModel):
    answers: List[AnswerItem] = Field(..., description="用户的回答列表")


class ResponseOut(BaseModel):
    id: str
    survey_id: str
    user_id: Optional[str]
    submitted_at: datetime
    answers: List[AnswerItem]
