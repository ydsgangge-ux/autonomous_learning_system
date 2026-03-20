# 🧠 自主智能学习系统 (ALS)

一个基于 AI 的自适应学习平台，具备知识图谱、间隔重复、主动探索、多模态内容摄入和**AGI进化循环**功能。

## ⚠️ 隐私与安全提示

**重要**：本项目数据存储在本地。部署或分享时，请注意：

- **禁止提交** API 密钥、令牌或敏感凭证到版本控制
- **始终使用** 环境变量（`.env` 文件）存储敏感配置
- **分享日志、截图或数据库文件前**，请检查是否包含敏感信息
- **本地存储**：所有学习进度、知识卡片和聊天历史都保存在您的设备上

---

## ✨ 新增：AGI 进化引擎 (v3.2)

系统新增**四大核心模块**，实现真正的AGI认知循环：

| 模块 | 功能 |
|------|------|
| **元认知审计** | 消除AI废话，强制深入底层原理 |
| **因果推理** | 提取因果链，构建逻辑骨架 |
| **沙盒验证** | 代码级验证，确保物理/数学正确性 |
| **跨域融合** | 打破知识孤岛，建立领域桥接 |

### 进化流程

```
原始输入 → 因果提取 → 沙盒验证 → 跨域合成 → 元认知审计 → 精炼知识
```

**示例**：输入"注塑压力过大会导致线束末端溢料"
- 因果层：`高压力 → 流体流速增加 → 模具间隙溢出`
- 沙盒层：验证压力公式 ΔP = ρv²/2
- 合成层：类比"大坝泄洪闸门溢流"或"乐器气压杂音"
- 审计层：剔除废话，确保结论可直接指导工艺

---

## 功能特点

### 核心学习系统
- **知识卡片** — AI 生成的自适应学习内容
- **间隔重复 (SM-2)** — 根据掌握程度智能安排复习时间
- **目标管理** — 创建和管理学习目标（汉字、词汇、概念、编程）

### AGI 核心 (v3.2)
- **进化编排层** — 协调四大模块的认知工厂
- **跨域知识融合** — 工业制造 ↔ 声学/音乐 ↔ 流体力学
- **元认知审计** — 拒绝平庸，产出专业严谨内容

### 知识管理
- **知识图谱** — 基于 NetworkX 的主题关联图
- **混合检索** — 向量搜索 (ChromaDB) + 知识图谱上下文
- **主动探索** — LLM 驱动的知识缺口检测和任务生成

### 用户界面
- **REST API** — 模块化端点的 FastAPI
- **网页界面** — 直观易用的浏览器界面（支持AGI进化）
- **命令行** — 交互式终端问答模式

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或使用 Poetry：

```bash
pip install poetry
poetry install
```

### 2. 配置环境

```bash
# 复制示例配置
copy .env.example .env

# 编辑 .env 文件，填入您的 API 凭证
# 必须：OPENAI_API_KEY（您的 LLM 提供商密钥）
# 可选：其他设置
```

> **安全提示**：切勿分享或提交 `.env` 文件到版本控制。请将 `.env` 添加到 `.gitignore`。

### 3. 初始化数据库

```bash
# 自动创建表（开发环境）
python -c "import asyncio; from db.session import init_db; asyncio.run(init_db())"

# 或使用 Alembic（生产环境）
alembic init db/migrations
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 4. 启动服务

```bash
# 启动 API 服务器和网页界面
python app.py

# 或直接使用 uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问应用

| 服务 | 地址 |
|------|------|
| **网页界面** | http://localhost:8000 |
| **API 文档** | http://localhost:8000/docs |
| **健康检查** | http://localhost:8000/health |

---

## 项目结构

```
autonomous_learning_system/
├── app.py                      # 应用入口
├── core/                       # 核心引擎
│   ├── metacognition.py       # 元认知审计
│   ├── causality.py           # 因果推理
│   ├── sandbox.py             # 沙盒验证
│   ├── synthesis.py           # 跨域融合
│   └── orchestrator.py       # 进化编排层
├── db/                        # SQLAlchemy 模型、会话
├── vector/                    # ChromaDB 存储
├── llm/                       # LLM 客户端
├── knowledge/                 # 知识图谱
├── perception/                # 思维导图、URL摄入
├── exploration/               # 缺口检测
├── planning/                  # SM-2 调度器
├── qa/                        # 问答系统
├── interfaces/                # API 路由
├── web_ui/                    # 网页界面
├── tests/                     # 测试
└── learning_data/             # JSON 学习数据
```

---

## API 端点

### AGI 进化引擎 (v3.2)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v2/evolve` | 一键进化（完整流程）|
| POST | `/api/v2/evolve/batch` | 批量进化 |
| GET | `/api/v2/evolve/domains` | 获取可用领域 |

### 知识卡片

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/knowledge/goals` | 创建学习目标 |
| GET | `/api/v1/knowledge/goals` | 列出所有目标 |
| POST | `/api/v1/knowledge/goals/{id}/populate` | 自动生成知识卡片 |
| GET | `/api/v1/knowledge/goals/{id}/progress` | 获取学习进度 |
| POST | `/api/v1/knowledge/goals/{id}/quiz` | 生成测试题 |
| POST | `/api/v1/knowledge/mastery/update` | 更新掌握程度 |

### 跨域融合

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/synthesis/domains` | 获取可用领域 |
| POST | `/api/v1/synthesis/analogy` | 生成跨域类比 |
| POST | `/api/v1/synthesis/auto` | 自动融合 |
| POST | `/api/v1/synthesis/rate` | 评分融合效果 |

### 问答系统

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v1/qa/ask` | 提问 |
| GET | `/api/v1/qa/history/{key}` | 获取聊天历史 |

### 探索与规划

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v1/exploration/gaps` | 检测知识缺口 |
| POST | `/api/v1/planning/reviews` | 提交复习评分 |

---

## 使用示例

### AGI 进化 (网页界面)

1. 启动服务：`python app.py`
2. 打开 http://localhost:8000
3. 点击导航栏 **⚡ AGI进化**
4. 输入待进化内容，点击"一键进化"

### AGI 进化 (API)

```python
import requests

response = requests.post("http://localhost:8000/api/v2/evolve", json={
    "content": "注塑压力过大会导致线束末端溢料。",
    "target_domain": "工业制造",
    "auto_synthesis": True
})

result = response.json()
print(result["final_output"])        # 精炼后的知识
print(result["insights"]["synthesis"]) # 跨域洞察
print(result["audit"]["logic_score"])  # 逻辑评分
```

### cURL

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/evolve" ^
  -H "Content-Type: application/json" ^
  -d "{\"content\": \"注塑压力过大会导致线束末端溢料\", \"target_domain\": \"工业制造\"}"
```

---

## 运行测试

```bash
pytest tests/ -v
```

---

## 数据存储

- **SQLite 数据库**：`als.db`（学习目标、卡片、进度）
- **向量存储**：`chroma_db/`（ChromaDB 嵌入向量）
- **学习数据**：`learning_data/*.json`

所有数据存储在本地。除 LLM API 调用生成内容外，不会向外部服务器发送数据。

---

## 依赖

- **Web 框架**：FastAPI、Uvicorn
- **数据库**：SQLAlchemy、SQLite (aiosqlite)
- **向量数据库**：ChromaDB、Sentence Transformers
- **LLM**：OpenAI SDK、Tenacity
- **定时任务**：APScheduler
- **知识图谱**：NetworkX
- **测试**：pytest、pytest-asyncio

完整列表见 `requirements.txt`。

---

## 其他文档

- [使用说明.md](使用说明.md) — 详细使用指南
- [Web界面使用说明.md](Web界面使用说明.md) — 网页界面使用指南
- [知识卡片系统详解.md](知识卡片系统详解.md) — 技术文档

---

## 免责声明

- 本系统使用 AI (LLM) 生成学习内容，请务必验证生成信息的准确性
- API 使用可能产生费用，具体取决于您的 LLM 服务提供商
- 请定期备份数据

---

**版本**: v3.2 (AGI Edition)  
**核心特性**: 元认知审计 | 因果推理 | 沙盒验证 | 跨域融合 | 进化编排
