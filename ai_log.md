# AI 编程使用日志

## 记录 1：项目初始化
* **时间**: 2026-04-01
* **使用工具**: Gemini 
* **使用提示词 (Prompt)**: 我想使用 uv+python 作为后端语言，使用 mongodb 作为数据库，请你先帮我完成整个项目系统的设计，给我一份清单... 好，我们先完成第一步，项目的初始化与环境的搭建 
* **得到的内容**: 项目目录结构设计、uv 依赖安装命令、FastAPI 结合 Motor 的数据库连接代码 
* **是否修改/修改了什么**: 暂无修改，直接运行成功，测试了根目录 API 返回正常。

## 记录 2：用户认证模块开发
* **时间**: 2026-04-01
* **使用工具**: Gemini
* **使用提示词 (Prompt)**: 接下来，完成步骤2，用户认证模块开发
* **得到的内容**: 包含了 JWT 鉴权配置、密码哈希安全工具 (`security.py`)、Pydantic 数据模型验证 (`user.py`)、注册与登录路由逻辑 (`auth.py`) 以及用于保护后续接口的依赖注入函数 (`deps.py`)。
* **是否修改/修改了什么**: (请根据你实际的运行情况填写，比如：无修改，直接运行测试通过，注册和登录 API 均返回了预期的数据和 Token。)


遇到的问题: 测试注册接口时报 500 错误，Traceback 显示 ValueError: password cannot be longer than 72 bytes。

如何解决: 发现是 passlib 与 bcrypt>=4.0.0 的版本冲突导致。通过 [降级 bcrypt 版本 / 替换为原生 bcrypt 逻辑] 解决。
=============================

测试指南
保存代码后，FastAPI 会自动重启。你可以前往 Swagger UI (http://127.0.0.1:8000/docs) 测试：

鉴权设置：首先调用 /api/auth/login 获取 Token。然后在 Swagger UI 页面右上角点击绿色的 "Authorize" 按钮，把 Token 粘贴进去。这样后续调用创建问卷等接口时，系统就能识别你的身份了。

创建问卷测试：展开 POST /api/surveys。你可以尝试传入包含多种题型、constraints (如 {"min_select": 2}) 和 jump_logic 的复杂 JSON 结构来测试数据库的兼容性。


获取详情测试：复制上一步生成的问卷 id，去测试 GET /api/surveys/{survey_id} 接口。这相当于文档要求的生成 /survey/XXXXXX 链接所需的数据接口 。

📝 AI 日志更新提醒：
测试跑通后，请在 ai_log.md 中添加记录 3：问卷创建与管理模块开发，说明我们利用 Pydantic 的灵活性实现了对动态题型和复杂限制条件的支持 。

测试完后告诉我，我们就可以向最复杂的答卷提交与后端硬核校验逻辑进发了！


========================

如果你现在直接点击 Authorize，很可能会遇到一个 422 Unprocessable Entity 的报错。这是我的疏忽！

原因在这里：
FastAPI 的这套 OAuth2 弹窗机制，默认发送请求的方式是 表单 (Form Data)。而我们在前面写的 login 接口中，使用的是 user: UserCreate，这会让 FastAPI 认为你要接收的是一个 JSON 格式的数据。两者对不上，就会报错。

为了让这个漂亮的绿锁（Authorize）按钮完美工作，我们需要把登录接口改为接收表单数据。

请打开 app/routers/auth.py，把 /login 接口替换成下面这样：

```py
# 顶部需要新导入 OAuth2PasswordRequestForm 和 Depends
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
# ... 其他导入保持不变 ...

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = db_instance.db
    # 注意：这里把 user.username 改成了 form_data.username
    db_user = await db.users.find_one({"username": form_data.username})
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    # 注意：这里把 user.password 改成了 form_data.password
    if not verify_password(form_data.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    # 生成 Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user["_id"])}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")
```

survey_id: 69cd37ebc370b1b8e16ed4af
