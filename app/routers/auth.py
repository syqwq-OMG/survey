from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.models.user import UserCreate, Token, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.database import db_instance
from app.core.config import settings
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    db = db_instance.db
    # 检查用户名是否已存在
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已被注册")

    # 创建新用户文档
    user_dict = {
        "username": user.username,
        "password_hash": get_password_hash(user.password),
        "created_at": datetime.now(timezone.utc) # 记录注册时间 [cite: 181]
    }
    
    result = await db.users.insert_one(user_dict)
    
    return UserResponse(
        id=str(result.inserted_id),
        username=user.username,
        created_at=user_dict["created_at"]
    )

@router.post("/login", response_model=Token)
async def login(user: UserCreate):
    db = db_instance.db
    # 查找用户
    db_user = await db.users.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    # 验证密码
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    # 生成 Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user["_id"])}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")