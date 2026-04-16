from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from typing import List, Optional

from app.models.question import QuestionBankCreate, QuestionBankResponse, QuestionShareUpdate
from app.core.deps import get_current_user
from app.database import db_instance

router = APIRouter(prefix="/api/questions", tags=["Questions"])

def serialize_question(doc) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc["creator_id"] = str(doc["creator_id"])
    if doc.get("parent_version_id"):
        doc["parent_version_id"] = str(doc["parent_version_id"])
    return doc

@router.post("", response_model=QuestionBankResponse)
async def create_question(question: QuestionBankCreate, current_user: dict = Depends(get_current_user)):
    db = db_instance.db
    doc = question.model_dump()
    
    new_original_id = str(ObjectId())
    doc["original_q_id"] = new_original_id
    doc["version"] = 1
    doc["creator_id"] = current_user["_id"]
    doc["is_shared"] = False
    doc["parent_version_id"] = None
    doc["created_at"] = datetime.now(timezone.utc)
    
    result = await db.question_bank.insert_one(doc)
    created_q = await db.question_bank.find_one({"_id": result.inserted_id})
    return serialize_question(created_q)

@router.get("", response_model=List[QuestionBankResponse])
async def get_questions(is_shared: Optional[bool] = None, current_user: dict = Depends(get_current_user)):
    db = db_instance.db
    
    if is_shared is True:
        query = {"is_shared": True}
    else:
        query = {"creator_id": current_user["_id"]}
        if is_shared is False:
            query["is_shared"] = False

    cursor = db.question_bank.find(query).sort("created_at", -1)
    results = await cursor.to_list(length=500)
    return [serialize_question(r) for r in results]

@router.post("/{q_id}/share", response_model=QuestionBankResponse)
async def toggle_share(q_id: str, update: QuestionShareUpdate, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(q_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    db = db_instance.db
    query = {"_id": ObjectId(q_id), "creator_id": current_user["_id"]}
    result = await db.question_bank.find_one_and_update(
        query,
        {"$set": {"is_shared": update.is_shared}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Question not found or unauthorized")
    return serialize_question(result)

@router.post("/{q_id}/versions", response_model=QuestionBankResponse)
async def create_new_version(q_id: str, question: QuestionBankCreate, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(q_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    db = db_instance.db
    old_q = await db.question_bank.find_one({"_id": ObjectId(q_id)})
    if not old_q:
        raise HTTPException(status_code=404, detail="Question not found")
    
    max_ver_doc = await db.question_bank.find_one(
        {"original_q_id": old_q["original_q_id"]},
        sort=[("version", -1)]
    )
    new_version = max_ver_doc["version"] + 1 if max_ver_doc else old_q["version"] + 1

    doc = question.model_dump()
    doc["original_q_id"] = old_q["original_q_id"]
    doc["version"] = new_version
    doc["creator_id"] = current_user["_id"]
    doc["is_shared"] = old_q["is_shared"]
    doc["parent_version_id"] = q_id
    doc["created_at"] = datetime.now(timezone.utc)

    result = await db.question_bank.insert_one(doc)
    created_q = await db.question_bank.find_one({"_id": result.inserted_id})
    return serialize_question(created_q)

@router.get("/{original_q_id}/history", response_model=List[QuestionBankResponse])
async def get_version_history(original_q_id: str, current_user: dict = Depends(get_current_user)):
    db = db_instance.db
    cursor = db.question_bank.find({"original_q_id": original_q_id}).sort("version", 1)
    results = await cursor.to_list(length=100)
    return [serialize_question(r) for r in results]

@router.get("/{q_id}/dependencies")
async def get_dependencies(q_id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(q_id):
        raise HTTPException(status_code=400, detail="Invalid ID")
    db = db_instance.db
    
    cursor = db.surveys.find({"questions.question_bank_id": q_id})
    results = await cursor.to_list(length=100)
    
    return [{"id": str(s["_id"]), "title": s["title"], "is_active": s.get("is_active", False)} for s in results]
