from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import connect_to_mongo, close_mongo_connection
from fastapi.staticfiles import StaticFiles  # 新增导入
from fastapi.responses import FileResponse  # 新增导入
from app.routers import auth, surveys, responses, stats, questions  # 新增导入 questions
from fastapi.middleware.cors import CORSMiddleware  # 1. 新增导入 CORS 中间件


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(title="问卷系统后端", lifespan=lifespan)


# === 2. 核心修复：添加跨域中间件 ===
app.add_middleware(
    CORSMiddleware,
    # 允许的跨域来源。开发阶段可以写 "*" 允许所有，或者明确写出 Vite 的地址
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # 允许所有请求头 (包括我们的 Authorization Token)
)


# 注册路由
app.include_router(auth.router)
app.include_router(surveys.router)  # 新增注册
app.include_router(responses.router)  # 新增注册
app.include_router(stats.router)  # 新增注册
app.include_router(questions.router)  # 新增注册

# === 新增：静态文件与前端入口挂载 ===
# 将 static 文件夹映射到 /static 路径
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")
