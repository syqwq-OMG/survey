from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import connect_to_mongo, close_mongo_connection
from fastapi.staticfiles import StaticFiles # 新增导入
from fastapi.responses import FileResponse  # 新增导入
from app.routers import auth, surveys, responses, stats  # 新增导入 surveys 和 stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="问卷系统后端", lifespan=lifespan)

# 注册路由
app.include_router(auth.router)
app.include_router(surveys.router) # 新增注册
app.include_router(responses.router) # 新增注册
app.include_router(stats.router) # 新增注册

# === 新增：静态文件与前端入口挂载 ===
# 将 static 文件夹映射到 /static 路径
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")