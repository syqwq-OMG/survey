from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


# 跳转逻辑模型
class JumpLogic(BaseModel):
    condition_value: Any = Field(description="触发跳转的条件值(如选项A或具体数字)")
    target_q_id: str = Field(description="满足条件时跳转到的目标题目ID")


# 统一的题目模型
class Question(BaseModel):
    q_id: str = Field(..., description="题目在问卷中的内部唯一ID，例如 'q1'")
    question_bank_id: Optional[str] = Field(None, description="引用的题库题目具体版本ID(如果为空，则表示是全新题目，后端会自动建库)")
    type: str = Field(..., description="题型：single, multiple, text, number")
    title: str = Field(..., description="题目内容")
    is_required: bool = Field(False, description="是否必填")
    is_shared: bool = Field(False, description="是否共享")
    options: Optional[List[str]] = Field(
        None, description="选项列表（适用于单选/多选）"
    )

    # 限制条件放在一个字典里，方便灵活扩展
    # 例如多选: {"min_select": 2, "max_select": 3}
    # 例如数字: {"min_value": 0, "max_value": 120, "is_integer": True}
    constraints: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="题型特定的限制条件"
    )

    jump_logic: Optional[List[JumpLogic]] = Field(
        default_factory=list, description="题目跳转逻辑"
    )


# 创建问卷的请求模型
class SurveyCreate(BaseModel):
    title: str = Field(..., min_length=1, description="问卷标题")
    description: Optional[str] = Field(None, description="问卷说明")
    is_anonymous: bool = Field(False, description="是否允许匿名填写")
    questions: List[Question] = Field(..., description="问卷包含的题目列表")


# 更新问卷状态的请求模型
class SurveyStatusUpdate(BaseModel):
    is_active: Optional[bool] = Field(None, description="是否发布/关闭问卷")
    deadline: Optional[datetime] = Field(None, description="问卷截止时间")


# 返回问卷详情的响应模型
class SurveyResponse(BaseModel):
    id: str
    creator_id: str
    title: str
    description: Optional[str]
    is_anonymous: bool
    is_active: bool
    deadline: Optional[datetime]
    created_at: datetime
    questions: List[Question]
