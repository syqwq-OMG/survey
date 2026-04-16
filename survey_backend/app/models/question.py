from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class QuestionBankCreate(BaseModel):
    """用于创建新题目或新版本的请求模型"""
    type: str = Field(..., description="题型：single, multiple, text, number")
    title: str = Field(..., description="题目内容")
    is_required: bool = Field(False, description="是否必填")
    options: Optional[List[str]] = Field(None, description="选项列表（适用于单选/多选）")
    constraints: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="题型特定的限制条件"
    )

class QuestionBankResponse(BaseModel):
    """返回的题目模型 (对应数据库中的完整文档)"""
    id: str = Field(..., description="该版本的唯一_id")
    original_q_id: str = Field(..., description="全局唯一标识符，关联各版本")
    version: int = Field(..., description="版本号")
    creator_id: str = Field(..., description="创建者ID")
    is_shared: bool = Field(False, description="是否发布到共享大厅")
    parent_version_id: Optional[str] = Field(None, description="上一版本的_id")
    created_at: datetime = Field(..., description="本版本创建时间")
    
    # 题目本身的内容
    type: str
    title: str
    is_required: bool
    options: Optional[List[str]]
    constraints: Optional[Dict[str, Any]]

class QuestionShareUpdate(BaseModel):
    is_shared: bool = Field(..., description="设置为共享(true)或私有(false)")
