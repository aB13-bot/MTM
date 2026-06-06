# AI Mother Community（AI 母亲社区）

一个基于 RAG 架构的 AI Agent 社区平台。用户可以发帖、评论、互动，并通过 `@Mother` 触发 AI 根据知识库和用户画像生成个性化回复。

---

## 目录

- [项目截图](#项目截图)
- [核心功能](#核心功能)
- [技术架构](#技术架构)
- [技术选型说明](#技术选型说明)
- [RAG 工作流程](#rag-工作流程)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [环境变量说明](#环境变量说明)
- [部署说明](#部署说明)
- [API 文档](#api-文档)

---

## 核心功能

- **用户系统**：JWT 认证，注册/登录/登出，用户画像（bio_memory）
- **社区互动**：发帖、评论、嵌套回复
- **AI 妈妈**：评论中 `@Mother` 触发，基于 RAG 检索知识库后生成回复
- **用户记忆**：AI 会记住用户的偏好和历史，个性化回复
- **知识库管理**：后台可向 ChromaDB 添加/更新知识文档

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
│              React + Vite + Tailwind CSS                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│                    Nginx（反向代理）                          │
│          /api/* → FastAPI    /* → React 静态文件             │
└──────────┬───────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────┐
│                  FastAPI 后端（mtm-backend）                  │
│                                                              │
│   ┌──────────────┐    ┌─────────────────────────────────┐   │
│   │  JWT 认证层   │    │         AI 回复模块              │   │
│   │  /auth/*     │    │                                 │   │
│   └──────────────┘    │  1. 接收 @Mother 触发信号        │   │
│                       │  2. 用户画像检索（bio_memory）    │   │
│   ┌──────────────┐    │  3. ChromaDB 语义检索            │   │
│   │  帖子/评论   │    │  4. Prompt 拼装                  │   │
│   │  CRUD API    │    │  5. SiliconFlow API 调用         │   │
│   └──────────────┘    │  6. 回复写入数据库               │   │
│                       └─────────────────────────────────┘   │
└──────┬───────────────────────┬──────────────────────────────┘
       │                       │
┌──────▼──────┐       ┌────────▼────────┐
│ PostgreSQL  │       │   ChromaDB      │
│(mtm-postgres│       │  向量数据库      │
│ 用户/帖子   │       │  知识库存储      │
│ 评论数据)   │       │  语义检索        │
└─────────────┘       └────────┬────────┘
                               │ Embedding
                      ┌────────▼────────┐
                      │sentence_transformers│
                      │paraphrase-multilingual│
                      │  -MiniLM-L12-v2  │
                      └─────────────────┘
                               │ LLM 调用
                      ┌────────▼────────┐
                      │ SiliconFlow API │
                      │  (DeepSeek 模型) │
                      └─────────────────┘
```

### 容器编排

```
Docker Compose
├── mtm-backend      FastAPI 应用（Python）
├── mtm-postgres     PostgreSQL 数据库
├── mtm-frontend     React 静态文件（构建产物）
└── mtm-nginx        Nginx 反向代理
```

---

## 技术选型说明

| 技术 | 选型原因 |
|------|---------|
| **FastAPI** | 原生异步支持（asyncpg），自动生成 OpenAPI 文档，Python 生态与 AI 库无缝集成，比 Django/Flask 更适合高并发 AI 服务 |
| **PostgreSQL** | 关系型数据满足用户/帖子/评论的复杂查询需求；外键约束保证数据一致性；asyncpg 提供高性能异步驱动 |
| **SQLAlchemy + Alembic** | ORM 屏蔽 SQL 细节，Alembic 管理数据库版本迁移，生产环境安全变更 schema |
| **ChromaDB** | 轻量级向量数据库，无需单独部署服务，直接嵌入 Python 进程；适合中小规模知识库的语义检索 |
| **sentence_transformers** | 开源多语言 Embedding 模型，paraphrase-multilingual-MiniLM-L12-v2 对中文支持好，可本地推理无需调用外部 API |
| **SiliconFlow / DeepSeek** | 国内可访问、低延迟、支持中文的 LLM API；DeepSeek 在中文理解和生成质量上表现优秀 |
| **JWT** | 无状态认证，服务端不需要存储 Session，适合前后端分离架构；token 可在前端持久化 |
| **React + Vite** | Vite 构建速度快，React 组件化方便维护；Tailwind 实现快速 UI 开发 |
| **Docker Compose** | 一键启动所有服务，开发/生产环境一致，方便云服务器部署 |
| **Nginx** | 统一入口，处理 HTTPS 终止、静态文件服务、反向代理，减少后端压力 |
| **阿里云香港** | 国内访问速度快，同时可访问境外 API（SiliconFlow 等） |

---

## RAG 工作流程

RAG（Retrieval-Augmented Generation，检索增强生成）是本项目 AI 回复的核心机制。

```
用户评论：@Mother 我最近睡眠很差怎么办？
              │
              ▼
    ┌─────────────────────┐
    │  1. Embedding 转换   │  将用户问题转为向量
    │  MiniLM-L12-v2      │  （768维浮点向量）
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  2. ChromaDB 检索    │  cosine 相似度搜索
    │  Top-K 相关文档      │  返回最相关的 K 条知识
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  3. 上下文拼装       │  知识文档 + 用户画像
    │  构建 Prompt         │  + 对话历史
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  4. LLM 生成回复     │  SiliconFlow / DeepSeek
    │  基于检索结果回答    │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │  5. 写入数据库       │  以 AI_MOTHER_USER_ID
    │  展示给用户          │  身份插入评论表
    └─────────────────────┘
```

**为什么用 RAG 而不是直接问 LLM？**

- LLM 的知识是训练截止日期前的，无法访问私有/专有知识库
- RAG 允许注入最新的、领域专属的内容（如育儿知识、社区规则）
- 检索到的内容作为上下文，让 LLM 的回答更有依据、更准确
- 降低幻觉（hallucination）风险

---

## 目录结构

```
MTM/
├── mothertalktome/                    # 后端
│   ├── alembic/                       # 数据库迁移
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── post.py
│   │   ├── auth/                      # JWT 认证模块
│   │   │   ├── dependencies.py
│   │   │   ├── api_messages.py
│   │   │   ├── jwt.py
│   │   │   ├── models.py
│   │   │   ├── password.py
│   │   │   ├── responses.py
│   │   │   ├── schemas.py
│   │   │   └── views.py
│   │   ├── core/                      # 核心配置
│   │   │   ├── config.py
│   │   │   ├── database_session.py
│   │   │   ├── lifespan.py
│   │   │   ├── metrics.py
│   │   │   └── models.py
│   │   ├── services/                  # 业务逻辑
│   │   │   └── llm_service.py         # RAG + LLM 调用
│   │   ├── schemas/
│   │   │   └── post.py
│   │   ├── models/
│   │   │   └── post.py
│   │   ├── probe/                     # 健康检查
│   │   └── main.py                    # FastAPI 入口
│   ├── chroma_db/                     # ChromaDB 向量数据库持久化
│   ├── data/                          # 知识库原始数据
│   ├── scripts/                       # 工具脚本
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
│
├── mothertalktome-frontend/           # 前端
│   ├── src/
│   │   ├── assets/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── index.html
│   ├── tailwind.config.js
│   └── vite.config.js
│
└── docker-compose.yml                 # 统一编排所有服务
```

---

## 快速开始

### 前置条件

- Docker & Docker Compose
- （可选）Node.js 18+ 用于本地前端开发

### 1. 克隆并配置环境变量

```bash
git clone <your-repo-url>
cd <project-root>
cp .env.example .env
# 编辑 .env，填入数据库密码、JWT Secret、SiliconFlow API Key 等
```

### 2. 启动所有服务

```bash
docker compose up -d --build
```

### 3. 初始化数据库

```bash
# 运行 Alembic 迁移
docker exec mtm-backend alembic upgrade head

# 插入 AI Mother 系统用户（必须在迁移后执行）
docker exec -i mtm-postgres psql \
  -U $DB_USER \
  -d default_db \
  -c "INSERT INTO auth_user (user_id, email, hashed_password, created_at, updated_at, bio_memory)
      VALUES ('$AI_MOTHER_USER_ID', 'ai-mother@internal.system',
              'PLACEHOLDER', NOW(), NOW(), 'AI Mother system account')
      ON CONFLICT (user_id) DO NOTHING;"
```

### 4. 访问应用

- 前端：`http://localhost` 或 `https://your-domain.com`
- API 文档：`http://localhost:8000/docs`

---

## 环境变量说明

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://rDGJeEDqAz:PASSWORD@mtm-postgres:5432/default_db
DB_USER=rDGJeEDqAz

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# AI
AI_MOTHER_USER_ID=448220c2-c3cf-480a-9aa9-dcbc051b8281
SILICONFLOW_API_KEY=your-api-key-here
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3

# ChromaDB
CHROMA_PERSIST_DIR=/app/chroma
```

---

## 部署说明

项目部署在**阿里云香港轻量服务器**，使用 Docker Compose 管理所有服务。

```bash
# 服务器首次部署
git clone <repo> && cd <project>
cp .env.example .env && vim .env   # 填写生产环境变量
docker compose up -d --build

# 更新部署
git pull
docker compose up -d --build --no-deps mtm-backend  # 只重建后端
```

**数据持久化：** PostgreSQL 数据和 ChromaDB 向量数据通过 Docker Volume 持久化，容器重启不丢失数据。

---

## API 文档

启动后访问 `http://localhost:8000/docs` 查看完整的 Swagger UI 文档。

主要接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 登录，返回 JWT token |
| GET | `/posts` | 获取帖子列表 |
| POST | `/posts` | 发布新帖子 |
| POST | `/posts/{id}/comments` | 发表评论（含 @Mother 触发） |
| GET | `/posts/{id}/comments` | 获取帖子评论 |

---

## License

MIT
