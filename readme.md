# survey
---
一个在线问卷系统，支持用户注册登录、问卷创建、问卷填写、跳转逻辑以及数据统计等功能。前端使用 Vue.js，后端使用 Python 和 FastAPI，数据库使用 MongoDB。


```
.
├── documents       # 文档说明
├── readme.md
├── test            # 测试代码
├── survey-frontend # 前端代码
└── survey_backend  # 后端代码
```


Ran command: `uv`

Since `uv` was extracted locally to `D:\Tools\` and isn't mapped to your global environment PATH yet, running `uv` directly throws an error.

Here are the precise commands you need to run to start both services. You should open **two separate PowerShell terminals** for this:

### 1. Start the Backend Service
Open your first terminal and run the following commands to navigate to your backend directory and use the exact static path for `uv` to start the server:

```powershell
cd D:\Workspace\survey\survey_backend
D:\Tools\uv\uv.exe run uvicorn app.main:app --reload
```
*The backend API will start running (typically on `http://localhost:8000`).*

### 2. Start the Frontend Service
Open your second terminal and run the following commands to start the Vue.js interface:

```powershell
cd D:\Workspace\survey\survey-frontend
npm run dev
```
*The terminal will output a local network address (typically `http://localhost:5173`) which you can click to see the app!*

---
**💡 Note on MongoDB:** 
I started the MongoDB database service silently in the background for you earlier. If you ever restart your computer and need to start the database again, just run this command beforehand:
```powershell
D:\Tools\mongodb-win32-x86_64-windows-7.0.5\bin\mongod.exe --dbpath D:\Tools\mongodb_data
```