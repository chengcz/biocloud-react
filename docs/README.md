# BioCloud - 生物信息在线分析平台

## 项目概述

BioCloud 是一个基于 LLM 的生物信息在线分析平台，提供智能化的数据分析服务。

### 核心功能

- **LLM 智能解析**: 自动判断用户需求，调用后台分析工具
- **用户管理**: 注册、登录、个人信息管理
- **权限管理**: 三层结构（组织 → 部门 → 亚组 → 用户）
- **ChatGPT 风格界面**: 深色主题，左侧对话列表，右侧聊天区

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + TailwindCSS + Zustand |
| 后端 | FastAPI + SQLAlchemy (async) + Alembic |
| 数据库 | PostgreSQL |
| LLM | LiteLLM (支持 Claude/OpenAI/本地模型) |
| 可视化 | Plotly.js |

## 快速开始

### 环境要求

- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### 启动服务

```bash
# 克隆项目
cd /path/to/biocloud

# 启动所有服务
docker-compose up --build

# 访问服务
# 前端: http://localhost:5173
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
# Adminer: http://localhost:8080
```

### 环境变量

创建 `backend/.env` 文件:

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://username:password@postgres:5432/vector

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM API Keys
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key

# CORS
CORS_ORIGINS=["http://localhost:5173"]
```

## 项目结构

```
biocloud/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── models/        # 数据库模型
│   │   ├── schemas/       # Pydantic 模式
│   │   ├── services/      # 业务逻辑
│   │   ├── core/          # 核心模块 (安全、异常)
│   │   └── config/        # 配置
│   ├── alembic/           # 数据库迁移
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/           # API 客户端
│   │   ├── components/    # React 组件
│   │   ├── pages/         # 页面组件
│   │   ├── stores/        # Zustand 状态
│   │   ├── hooks/         # 自定义 Hooks
│   │   └── types/         # TypeScript 类型
│   └── package.json
├── docs/                   # 文档
└── docker-compose.yml
```

## API 端点

### 认证

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/logout | 用户登出 |
| POST | /api/v1/auth/refresh | 刷新 Token |
| GET | /api/v1/auth/me | 获取当前用户信息 |

### 用户管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/v1/users | 用户列表 |
| POST | /api/v1/users | 创建用户 |
| GET | /api/v1/users/{id} | 用户详情 |
| PUT | /api/v1/users/{id} | 更新用户 |
| DELETE | /api/v1/users/{id} | 删除用户 |

### 部门管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/v1/departments | 部门树 |
| POST | /api/v1/departments | 创建部门 |
| PUT | /api/v1/departments/{id} | 更新部门 |
| DELETE | /api/v1/departments/{id} | 删除部门 |

### 对话

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/v1/conversations | 对话列表 |
| POST | /api/v1/conversations | 创建对话 |
| GET | /api/v1/conversations/{id} | 对话详情 |
| DELETE | /api/v1/conversations/{id} | 删除对话 |
| POST | /api/v1/conversations/{id}/messages | 发送消息 (SSE 流式) |

## 数据库模型

### 用户与权限

- `sys_user` - 用户表
- `sys_dept` - 部门表 (层级结构)
- `sys_post` - 岗位表
- `sys_role` - 角色表
- `sys_permission` - 权限表

### 对话与分析

- `conversations` - 对话表
- `messages` - 消息表
- `analyses` - 分析任务表
- `uploaded_files` - 上传文件表

## 开发指南

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 安全

- JWT 短期 Token + Refresh Token
- Argon2 密码哈希
- API 速率限制
- 文件上传验证
- SQL 注入防护 (SQLAlchemy 参数化)
- XSS 防护 (Markdown 消毒)
- CORS 白名单

## 许可证

MIT License