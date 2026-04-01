from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.models.stat import SurveyStatOut, QuestionStat
from app.core.deps import get_current_user
from app.database import db_instance

router = APIRouter(prefix="/api/surveys", tags=["Statistics"])


@router.get("/{survey_id}/stats", response_model=SurveyStatOut)
async def get_survey_stats(
    survey_id: str, current_user: dict = Depends(get_current_user)  # 强制要求登录
):
    db = db_instance.db

    # 1. 验证问卷是否存在
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=400, detail="无效的问卷 ID")
    survey = await db.surveys.find_one({"_id": ObjectId(survey_id)})
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")

    # 2. 权限校验：只有创建者可以查看统计结果
    if str(survey["creator_id"]) != str(current_user["_id"]):
        raise HTTPException(
            status_code=403, detail="无权访问，只有问卷创建者可以查看统计结果"
        )

    # 3. 获取该问卷的所有答卷数据
    cursor = db.responses.find({"survey_id": ObjectId(survey_id)})
    responses = await cursor.to_list(length=None)

    # 4. 初始化统计存储结构（根据问卷自身的题目定义）
    stats_map = {}
    for q in survey.get("questions", []):
        stat = {
            "q_id": q["q_id"],
            "type": q["type"],
            "title": q["title"],
            "total_responses": 0,
        }
        if q["type"] in ["single", "multiple"]:
            stat["option_counts"] = {opt: 0 for opt in q.get("options", [])}
        elif q["type"] == "text":
            stat["text_answers"] = []
        elif q["type"] == "number":
            stat["_sum"] = 0.0  # 临时字段，用于后续算平均值

        stats_map[q["q_id"]] = stat

    # 5. 遍历答卷，累加统计数据
    for resp in responses:
        for ans in resp.get("answers", []):
            q_id = ans["q_id"]
            val = ans["value"]

            # 过滤掉不在题目定义里的脏数据
            if q_id not in stats_map:
                continue

            target_stat = stats_map[q_id]
            target_stat["total_responses"] += 1
            q_type = target_stat["type"]

            # 单选题统计 [cite: 271-272]
            if q_type == "single":
                if val in target_stat["option_counts"]:
                    target_stat["option_counts"][val] += 1

            # 多选题统计 [cite: 274-275]
            elif q_type == "multiple":
                if isinstance(val, list):
                    for v in val:
                        if v in target_stat["option_counts"]:
                            target_stat["option_counts"][v] += 1

            # 文本题统计 [cite: 276-277]
            elif q_type == "text":
                if val is not None and str(val).strip() != "":
                    target_stat["text_answers"].append(str(val))

            # 数字题统计（累加求和）
            elif q_type == "number":
                if val is not None:
                    try:
                        target_stat["_sum"] += float(val)
                    except ValueError:
                        pass

    # 6. 处理最终结果（比如计算数字题的平均值） [cite: 278]
    result_questions = []
    for q_id, stat in stats_map.items():
        if stat["type"] == "number":
            if stat["total_responses"] > 0:
                stat["average"] = stat["_sum"] / stat["total_responses"]
            else:
                stat["average"] = 0.0
            del stat["_sum"]  # 清理临时字段

        result_questions.append(QuestionStat(**stat))

    # 7. 返回总统计结果
    return SurveyStatOut(
        survey_id=survey_id,
        total_submissions=len(responses),
        questions=result_questions,
    )
