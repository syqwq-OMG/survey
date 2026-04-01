from pydantic import BaseModel
from typing import List, Dict, Optional

class QuestionStat(BaseModel):
    q_id: str
    type: str
    title: str
    total_responses: int = 0  # 该题目的总回答人数 [cite: 273]
    
    # 针对选择题：记录每个选项被选择的次数 [cite: 272, 275]
    option_counts: Optional[Dict[str, int]] = None
    
    # 针对文本填空题：记录所有填写的内容 [cite: 277]
    text_answers: Optional[List[str]] = None
    
    # 针对数字填空题：计算出的平均值 [cite: 278]
    average: Optional[float] = None

class SurveyStatOut(BaseModel):
    survey_id: str
    total_submissions: int
    questions: List[QuestionStat]