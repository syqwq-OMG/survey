使用 **Python (通过 `uv` 管理)** 搭配 **MongoDB** 是一个非常现代且高效的选择。`uv` 极快的依赖管理和 Python 生态中强大的后端框架（如 FastAPI）能让你在这个项目中事半功倍。

根据项目文档的要求，我为你设计了第一阶段的系统架构和 MongoDB 数据模型，并梳理了一份详细的开发任务清单。

---

### 一、 技术栈推荐

[cite_start]既然你确定了 Python + MongoDB [cite: 75, 76]，我建议采用以下具体框架组合：
* **依赖管理与运行环境**：`uv` (极速，替代 pip/poetry)。
* [cite_start]**Web 框架**：`FastAPI`。它原生支持异步，且其基于 Pydantic 的数据验证完美契合问卷系统复杂的表单校验需求 [cite: 261]。
* **数据库驱动 / ODM**：`Motor` (MongoDB 官方异步驱动) 或 `Beanie` (基于 Motor 和 Pydantic 的 ODM，能极大简化 MongoDB 在 FastAPI 中的使用)。
* [cite_start]**前端**：纯 HTML + Vanilla JS，或者简单的 Vue.js/React 页面（项目对前端界面要求不高 [cite: 11, 78]）。

---

### 二、 MongoDB 数据库设计 (Schema 设计)

[cite_start]文档强调**不要将所有数据存在一个集合，也不要过度冗余** [cite: 86, 87]。结合 NoSQL 的特性，我建议设计 **3 个核心集合 (Collections)**。

#### 1. `users` 集合 (用户信息)
[cite_start]用于处理系统的注册、登录和鉴权 [cite: 171]。
* `_id`: ObjectId
* [cite_start]`username`: String (唯一索引) [cite: 179]
* [cite_start]`password_hash`: String (加密后的密码) [cite: 180]
* [cite_start]`created_at`: DateTime (注册时间) [cite: 181]

#### 2. `surveys` 集合 (问卷及题目定义)
**设计思路：** 将“题目(Questions)”作为数组嵌套在“问卷(Survey)”文档中。
[cite_start]**为什么这样设计：** 问卷和它的题目是强聚合关系，通常是一起读取的。嵌套设计可以避免关系型数据库中频繁的 JOIN 操作，充分发挥 MongoDB 的文档模型优势 [cite: 90, 91, 93]。

* `_id`: ObjectId
* [cite_start]`creator_id`: ObjectId (关联 `users` 集合，仅创建者可见) [cite: 175, 182]
* [cite_start]`title`: String [cite: 186]
* [cite_start]`description`: String [cite: 187]
* [cite_start]`is_anonymous`: Boolean [cite: 188]
* [cite_start]`deadline`: DateTime (截止时间) [cite: 192]
* [cite_start]`is_active`: Boolean (问卷是否关闭) [cite: 194]
* [cite_start]`questions`: Array of Objects (题目列表) [cite: 200]
    * `q_id`: String (题目内部唯一ID)
    * [cite_start]`type`: String ("single", "multiple", "text", "number") [cite: 202, 203, 214, 229]
    * `title`: String
    * [cite_start]`is_required`: Boolean [cite: 212]
    * [cite_start]`options`: Array of Strings (针对选择题) [cite: 211]
    * `constraints`: Object (针对特定题型的限制条件)
        * [cite_start]多选题限制：`min_select`, `max_select`, `exact_select` [cite: 223-226]
        * [cite_start]文本题限制：`min_length`, `max_length` [cite: 234, 236]
        * [cite_start]数字题限制：`min_value`, `max_value`, `is_integer` [cite: 237-240]
    * [cite_start]`jump_logic`: Array of Objects (跳转逻辑) [cite: 245, 250]
        * `condition_value`: Any (触发跳转的选项值或填空值)
        * [cite_start]`target_q_id`: String (满足条件时跳转到的题目ID) [cite: 248]

#### 3. `responses` 集合 (答卷数据)
[cite_start]**设计思路：** 必须与问卷分离。随着填写人数增加，答卷数据会快速膨胀，如果嵌套在 `surveys` 中会导致单个文档超出 MongoDB 的 16MB 限制 [cite: 86]。

* `_id`: ObjectId
* `survey_id`: ObjectId (关联 `surveys` 集合)
* [cite_start]`user_id`: ObjectId (如果未匿名且已登录，记录填写者) [cite: 198, 266]
* `submitted_at`: DateTime
* `answers`: Array of Objects (用户的具体回答)
    * `q_id`: String (对应题目ID)
    * `value`: Any (单选是字符串，多选是数组，填空是文本或数字)

---

### 三、 第一阶段开发任务清单 (基于 uv + Python)

[cite_start]你可以按照以下步骤逐步推进，请特别注意随时记录 AI 的使用情况 [cite: 96]。

#### 步骤 1：项目初始化与环境搭建
- [x] 使用 `uv` 初始化 Python 项目 (`uv init`)。
- [x] 使用 `uv add` 安装核心依赖：`fastapi`, `uvicorn`, `motor` (或 `beanie`), `pydantic`, `pyjwt`, `passlib`。
- [x] 搭建本地 MongoDB 数据库并测试连接。
- [x] [cite_start]**创建 AI 使用日志文件** (例如 `ai_log.md`)，从第一行代码开始记录你的 Prompt 和 AI 生成的内容 [cite: 98-104]。

#### 步骤 2：用户认证模块开发
- [x] 编写 Pydantic Schema，定义用户注册和登录的输入结构。
- [x] 实现密码哈希逻辑（切忌明文存储密码）。
- [x] [cite_start]开发 API：`POST /api/register` 和 `POST /api/login` [cite: 173, 174]。
- [x] 实现 JWT Token 签发与鉴权中间件。

#### 步骤 3：问卷管理模块开发 (核心 CRUD)
- [ ] 编写问卷及复杂题目的 Pydantic 校验模型（确保支持各题型的 `constraints` 和 `jump_logic`）。
- [ ] [cite_start]开发 API：`POST /api/surveys` (创建问卷) [cite: 184]。
- [ ] [cite_start]开发 API：`GET /api/surveys` (获取当前用户的问卷列表) [cite: 190]。
- [ ] [cite_start]开发 API：`GET /api/surveys/{id}` (获取单份问卷详情，用于生成分享链接) [cite: 195, 196]。
- [ ] [cite_start]开发 API：`PUT /api/surveys/{id}/status` (发布/关闭问卷) [cite: 191, 194]。

#### 步骤 4：问卷填写与校验逻辑
- [ ] [cite_start]开发 API：`POST /api/surveys/{id}/responses` (提交答卷) [cite: 262]。
- [ ] [cite_start]**实现后端硬核校验逻辑 (重点)**：在保存答卷前，遍历提交的答案，根据问卷 schema 中的 `constraints` (必答、多选数量、字数、数字范围等) 进行严格校验，不符合则抛出 400 错误 [cite: 213, 227, 244, 261]。
- [ ] [cite_start]*注：跳转逻辑 (`jump_logic`) 主要在前端填写时体现（隐藏/显示题目），后端主要校验最终提交的答案序列是否合理 [cite: 254, 260]。*

#### 步骤 5：数据统计模块开发
- [ ] 开发 API：`GET /api/surveys/{id}/stats`。
- [ ] 编写 MongoDB 聚合查询 (Aggregation Pipeline)：
    - [cite_start]统计单选题的各选项人数 [cite: 271, 272]。
    - [cite_start]统计多选题的各选项被选次数 [cite: 274, 275]。
    - [cite_start]获取填空题的所有内容，并在数字题时使用聚合函数 `$avg` 计算平均值 [cite: 276-278]。

#### 步骤 6：前端对接与测试
- [ ] [cite_start]编写简单的 HTML/JS 页面调用上述接口 [cite: 11, 78]。
- [ ] [cite_start]编写测试用例（API 测试或手工测试均可），覆盖问卷创建、跳转逻辑、校验拦截和统计功能 [cite: 121-128]。
- [ ] [cite_start]记录测试步骤和输入输出 [cite: 150-153]。

#### 步骤 7：编写项目报告 (交付物)
- [ ] [cite_start]整理数据库设计说明（解释为何不用关系型，为何适合 MongoDB）[cite: 89-93]。
- [ ] [cite_start]整理 API 文档和跳转/校验逻辑说明 [cite: 146, 147, 159, 160]。
- [ ] [cite_start]总结 AI 使用说明（AI 帮了什么、错了什么、你改了什么）[cite: 114-118]。

---

对于后端的 Web 框架，你更倾向于使用原生异步且生态火热的 **FastAPI**，还是有其他熟悉的 Python 框架（比如 Flask 或 Django）？确定框架后，我们可以直接开始针对具体模块生成基础代码和详细的提示词 (Prompt) 策略。