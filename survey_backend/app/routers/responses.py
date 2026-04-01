# app/routers/responses.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.models.response import ResponseCreate, ResponseOut
from app.core.deps import get_optional_current_user
from app.database import db_instance

router = APIRouter(prefix="/api/surveys", tags=["Responses"])

@router.post("/{survey_id}/responses", response_model=ResponseOut)
async def submit_response(
    survey_id: str, 
    response_data: ResponseCreate, 
    current_user: dict = Depends(get_optional_current_user)
):
    db = db_instance.db
    
    # 1. 查找问卷是否存在及是否开放
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=400, detail="无效的问卷 ID")
    survey = await db.surveys.find_one({"_id": ObjectId(survey_id)})
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
        
    if not survey.get("is_active", False):
        raise HTTPException(status_code=403, detail="该问卷尚未发布或已关闭")
        
    # 2. 匿名权限检查
    if not survey.get("is_anonymous", False) and current_user is None:
        raise HTTPException(status_code=401, detail="该问卷不允许匿名填写，请先登录")

    # 3. 核心校验逻辑准备
    questions_map = {q["q_id"]: q for q in survey.get("questions", [])}
    submitted_answers_map = {ans.q_id: ans.value for ans in response_data.answers}

    # 4. 逐题校验
    for q_id, q_def in questions_map.items():
        q_type = q_def.get("type")
        is_required = q_def.get("is_required", False)
        constraints = q_def.get("constraints", {})
        value = submitted_answers_map.get(q_id)

        # 4.1 必答校验
        if is_required and (value is None or value == "" or value == []):
            # 注意：实际业务中如果有“跳转逻辑”导致题目被跳过，这里可能需要结合前端传来的展现路径。
            # 为简化第一阶段，我们严格要求必答题必须有值。
            raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 是必填项")

        if value is None:
            continue # 非必填且没填，直接跳过后续校验

        # 4.2 单选题校验
        if q_type == "single":
            if value not in q_def.get("options", []):
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 的选项不合法")

        # 4.3 多选题校验
        elif q_type == "multiple":
            if not isinstance(value, list):
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 格式错误，应为列表")
            # 检查选项是否都在允许范围内
            if not all(v in q_def.get("options", []) for v in value):
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 存在不合法选项")
            # 数量限制校验
            select_count = len(value)
            if "min_select" in constraints and select_count < constraints["min_select"]:
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 至少选择 {constraints['min_select']} 项")
            if "max_select" in constraints and select_count > constraints["max_select"]:
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 最多选择 {constraints['max_select']} 项")

        # 4.4 文本填空题校验
        elif q_type == "text":
            if not isinstance(value, str):
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 必须是文本")
            text_length = len(value)
            if "min_length" in constraints and text_length < constraints["min_length"]:
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 最少输入 {constraints['min_length']} 个字符")
            if "max_length" in constraints and text_length > constraints["max_length"]:
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 最多输入 {constraints['max_length']} 个字符")

        # 4.5 数字填空题校验
        elif q_type == "number":
            # 尝试转换为浮点数
            try:
                num_value = float(value)
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 必须是有效数字")
                
            if constraints.get("is_integer", False) and not num_value.is_integer():
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 必须是整数")
                
            if "min_value" in constraints and num_value < constraints["min_value"]:
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 的值不能小于 {constraints['min_value']}")
            if "max_value" in constraints and num_value > constraints["max_value"]:
                raise HTTPException(status_code=400, detail=f"题目 '{q_def['title']}' 的值不能大于 {constraints['max_value']}")

    # 5. 校验全部通过，保存答卷 [cite: 263]
    response_doc = {
        "survey_id": ObjectId(survey_id),
        "user_id": current_user["_id"] if current_user else None,
        "submitted_at": datetime.now(timezone.utc),
        "answers": [ans.model_dump() for ans in response_data.answers]
    }
    
    result = await db.responses.insert_one(response_doc)
    
    # 格式化返回结果
    response_doc["id"] = str(result.inserted_id)
    response_doc["survey_id"] = str(response_doc.pop("survey_id"))
    response_doc["user_id"] = str(response_doc["user_id"]) if response_doc["user_id"] else None
    
    return response_doc