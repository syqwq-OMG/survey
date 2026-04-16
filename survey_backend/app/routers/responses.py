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
    current_user: dict = Depends(get_optional_current_user),
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

    # ===== 新增：检查是否超过截止时间 =====
    deadline = survey.get("deadline")
    if deadline:
        # 确保时间都在 UTC 时区下比较
        if datetime.now(timezone.utc) > deadline.replace(tzinfo=timezone.utc):
            raise HTTPException(
                status_code=403, detail="该问卷已超过截止时间，停止收集"
            )

    # 2. 匿名权限检查
    if not survey.get("is_anonymous", False) and current_user is None:
        raise HTTPException(status_code=401, detail="该问卷不允许匿名填写，请先登录")

    # 3. 核心校验逻辑准备
    questions = survey.get("questions", [])
    submitted_answers_map = {ans.q_id: ans.value for ans in response_data.answers}

    # 获取题库的 original_id 映射
    qb_ids = [ObjectId(q["question_bank_id"]) for q in questions if q.get("question_bank_id") and ObjectId.is_valid(q["question_bank_id"])]
    qb_map = {}
    if qb_ids:
        cursor = db.question_bank.find({"_id": {"$in": qb_ids}})
        # max pool length of 500 questions per survey
        qb_docs = await cursor.to_list(length=500)
        for doc in qb_docs:
            qb_map[str(doc["_id"])] = doc.get("original_q_id")

    # 用于记录被跳转逻辑跳过的题目 ID
    hidden_q_ids = set()

    # 4. 逐题校验
    for i, q_def in enumerate(questions):
        q_id = q_def["q_id"]
        # ===== 核心修复：如果这道题被前面的逻辑跳过了，直接放行，不进行任何校验 =====
        if q_id in hidden_q_ids:
            continue
        q_type = q_def.get("type")
        is_required = q_def.get("is_required", False)
        constraints = q_def.get("constraints", {})
        value = submitted_answers_map.get(q_id)

        # 4.1 必答校验
        if is_required and (value is None or value == "" or value == []):
            # 注意：实际业务中如果有“跳转逻辑”导致题目被跳过，这里可能需要结合前端传来的展现路径。
            # 为简化第一阶段，我们严格要求必答题必须有值。
            raise HTTPException(
                status_code=400, detail=f"题目 '{q_def['title']}' 是必填项"
            )

        if value is None or value == "":
            continue  # 非必填且没填，直接跳过后续校验

        # 4.2 单选题校验
        if q_type == "single":
            if value not in q_def.get("options", []):
                raise HTTPException(
                    status_code=400, detail=f"题目 '{q_def['title']}' 的选项不合法"
                )

        # 4.3 多选题校验
        elif q_type == "multiple":
            if not isinstance(value, list):
                raise HTTPException(
                    status_code=400,
                    detail=f"题目 '{q_def['title']}' 格式错误，应为列表",
                )
            # 检查选项是否都在允许范围内
            if not all(v in q_def.get("options", []) for v in value):
                raise HTTPException(
                    status_code=400, detail=f"题目 '{q_def['title']}' 存在不合法选项"
                )
            # 数量限制校验
            select_count = len(value)
            if "min_select" in constraints and select_count < constraints["min_select"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"题目 '{q_def['title']}' 至少选择 {constraints['min_select']} 项",
                )
            if "max_select" in constraints and select_count > constraints["max_select"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"题目 '{q_def['title']}' 最多选择 {constraints['max_select']} 项",
                )

        # 4.4 文本填空题校验
        elif q_type == "text":
            if not isinstance(value, str):
                raise HTTPException(
                    status_code=400, detail=f"题目 '{q_def['title']}' 必须是文本"
                )
            text_length = len(value)
            if "min_length" in constraints and text_length < constraints["min_length"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"题目 '{q_def['title']}' 最少输入 {constraints['min_length']} 个字符",
                )
            if "max_length" in constraints and text_length > constraints["max_length"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"题目 '{q_def['title']}' 最多输入 {constraints['max_length']} 个字符",
                )

        # 4.5 数字填空题校验
        elif q_type == "number":
            # 尝试转换为浮点数
            try:
                num_value = float(value)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=400, detail=f"题目 '{q_def['title']}' 必须是有效数字"
                )

            if constraints.get("is_integer", False) and not num_value.is_integer():
                raise HTTPException(
                    status_code=400, detail=f"题目 '{q_def['title']}' 必须是整数"
                )

            if "min_value" in constraints and num_value < constraints["min_value"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"题目 '{q_def['title']}' 的值不能小于 {constraints['min_value']}",
                )
            if "max_value" in constraints and num_value > constraints["max_value"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"题目 '{q_def['title']}' 的值不能大于 {constraints['max_value']}",
                )

        # ===== 新增：校验通过后，计算当前题的跳转逻辑，将被跳过的题目加入 hidden_q_ids =====
        # ===== 计算当前题的跳转逻辑 =====
        jump_logic = q_def.get("jump_logic", [])
        target_id = None
        for logic in jump_logic:
            cond_val = logic.get("condition_value")
            t_id = logic.get("target_q_id")

            if q_type == "single" and value == cond_val:
                target_id = t_id
                break
            elif (
                q_type == "multiple"
                and isinstance(value, list)
                and isinstance(cond_val, list)
            ):
                # 后端多选跳转逻辑：cond_val 不为空，且是 value 的子集
                if len(cond_val) > 0 and set(cond_val).issubset(set(value)):
                    target_id = t_id
                    break
            elif q_type == "number":
                try:
                    if float(value) == float(cond_val):
                        target_id = t_id
                        break
                except (ValueError, TypeError):
                    pass

        # 如果命中了跳转目标，找到目标题目的索引，把中间的题全部标记为“跳过”
        if target_id:
            target_idx = -1
            for j in range(i + 1, len(questions)):
                if questions[j]["q_id"] == target_id:
                    target_idx = j
                    break
            if target_idx != -1:
                for j in range(i + 1, target_idx):
                    hidden_q_ids.add(questions[j]["q_id"])

    # 5. 校验全部通过，过滤掉被跳过的答案，保存有效答卷
    valid_answers = []
    for ans in response_data.answers:
        if ans.q_id not in hidden_q_ids:
            ans_dict = ans.model_dump()
            q_def = next((q for q in questions if q["q_id"] == ans.q_id), None)
            if q_def and q_def.get("question_bank_id"):
                qb_id_str = q_def["question_bank_id"]
                ans_dict["question_bank_original_id"] = qb_map.get(qb_id_str)
            valid_answers.append(ans_dict)

    response_doc = {
        "survey_id": ObjectId(survey_id),
        "user_id": current_user["_id"] if current_user else None,
        "submitted_at": datetime.now(timezone.utc),
        "answers": valid_answers,
    }

    result = await db.responses.insert_one(response_doc)

    # 格式化返回结果
    response_doc["id"] = str(result.inserted_id)
    response_doc["survey_id"] = str(response_doc.pop("survey_id"))
    response_doc["user_id"] = (
        str(response_doc["user_id"]) if response_doc["user_id"] else None
    )

    return response_doc
