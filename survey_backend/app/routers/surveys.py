from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List

from app.models.survey import SurveyCreate, SurveyResponse, SurveyStatusUpdate
from app.core.deps import get_current_user
from app.database import db_instance

router = APIRouter(prefix="/api/surveys", tags=["Surveys"])


def serialize_survey(survey_doc) -> dict:
    """辅助函数：将 MongoDB 返回的 _id 转换为字符串 id"""
    survey_doc["id"] = str(survey_doc.pop("_id"))
    survey_doc["creator_id"] = str(survey_doc["creator_id"])
    return survey_doc


@router.post("", response_model=SurveyResponse)
async def create_survey(
    survey: SurveyCreate, current_user: dict = Depends(get_current_user)
):
    """创建问卷"""
    db = db_instance.db
    survey_dict = survey.model_dump()

    # 补充后端自动生成的信息
    survey_dict["creator_id"] = current_user["_id"]
    survey_dict["created_at"] = datetime.now(timezone.utc)
    survey_dict["is_active"] = False  # 默认未发布
    survey_dict["deadline"] = None

    result = await db.surveys.insert_one(survey_dict)

    # 获取刚插入的数据并返回
    created_survey = await db.surveys.find_one({"_id": result.inserted_id})
    return serialize_survey(created_survey)


@router.get("", response_model=List[SurveyResponse])
async def get_my_surveys(current_user: dict = Depends(get_current_user)):
    """查看自己创建的问卷列表"""
    db = db_instance.db
    # 只能查询 creator_id 为当前用户的问卷
    cursor = db.surveys.find({"creator_id": current_user["_id"]})
    surveys = await cursor.to_list(length=100)
    return [serialize_survey(s) for s in surveys]


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey_detail(survey_id: str):
    """
    获取问卷详情 (用于填写问卷)
    注意：这个接口通常不需要鉴权，因为填写者可能是匿名或需要先看到问卷内容
    """
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=400, detail="无效的问卷 ID")

    db = db_instance.db
    survey = await db.surveys.find_one({"_id": ObjectId(survey_id)})

    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")

    return serialize_survey(survey)


@router.put("/{survey_id}/status", response_model=SurveyResponse)
async def update_survey_status(
    survey_id: str,
    status_update: SurveyStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """发布/关闭问卷，或设置截止时间"""
    if not ObjectId.is_valid(survey_id):
        raise HTTPException(status_code=400, detail="无效的问卷 ID")

    db = db_instance.db
    # 必须确保当前用户是问卷的创建者
    query = {"_id": ObjectId(survey_id), "creator_id": current_user["_id"]}

    update_data = {k: v for k, v in status_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供需要更新的字段")

    result = await db.surveys.find_one_and_update(
        query, {"$set": update_data}, return_document=True
    )

    if not result:
        raise HTTPException(status_code=404, detail="问卷不存在或无权修改")

    return serialize_survey(result)
