# BioCloud 架构设计文档

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Sidebar    │  │  Chat Area   │  │  Analysis Components │   │
│  │  (对话列表)   │  │  (消息流)     │  │  (Plotly可视化)       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST API / SSE
┌───────────────────────────────▼─────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Auth API    │  │  Chat API    │  │  Analysis API        │   │
│  │  (JWT认证)   │  │  (SSE流式)   │  │  (任务队列)          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    LLM Router (litellm)                   │   │
│  │     Claude API │ OpenAI API │ Local Models (Ollama)      │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     PostgreSQL Database                          │
│  sys_user │ sys_dept │ sys_role │ conversations │ analyses     │
└─────────────────────────────────────────────────────────────────┘
```

## 数据库设计

### ER 图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  sys_dept   │────<│  sys_user   │>────│  sys_role   │
│  (部门表)   │     │  (用户表)   │     │  (角色表)   │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                          │                    │
                          │                    │
                    ┌─────▼─────┐        ┌─────▼─────┐
                    │conversations│      │sys_permission│
                    │  (对话表)  │        │  (权限表)  │
                    └─────┬─────┘        └───────────┘
                          │
                    ┌─────▼─────┐
                    │ messages  │
                    │  (消息表) │
                    └───────────┘
```

### 核心表结构

#### 用户表 (sys_user)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | SERIAL | 主键 |
| user_name | VARCHAR(30) | 用户名 |
| password_hash | VARCHAR(255) | 密码哈希 |
| name | VARCHAR(30) | 姓名 |
| email | VARCHAR(50) | 邮箱 |
| dept_id | INTEGER | 部门ID |
| post_id | INTEGER | 岗位ID |
| leader_id | INTEGER | 上级领导ID |
| status | VARCHAR(10) | 状态 |

#### 部门表 (sys_dept)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(50) | 部门名称 |
| parent_id | INTEGER | 父部门ID |
| dept_path | VARCHAR(500) | 部门路径(.1.5.12.) |
| leader_user_id | INTEGER | 负责人ID |

#### 角色表 (sys_role)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(30) | 角色名称 |
| role_key | VARCHAR(100) | 角色标识 |
| is_admin | BOOLEAN | 是否管理员 |
| data_scope_type | VARCHAR(20) | 数据权限范围 |

## API 设计

### RESTful API 规范

```
GET    /api/v1/users           # 获取用户列表
POST   /api/v1/users           # 创建用户
GET    /api/v1/users/{id}      # 获取单个用户
PUT    /api/v1/users/{id}      # 更新用户
DELETE /api/v1/users/{id}      # 删除用户
```

### 响应格式

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "用户名已存在"
  }
}
```

## 权限系统

### 三层权限结构

```
组织 (Organization)
  └── 部门 (Department)
        └── 亚组 (Subgroup)
              └── 用户 (User)
```

### 数据权限范围

| 类型 | 描述 |
|------|------|
| self | 仅本人数据 |
| dept | 本部门数据 |
| dept_with_child | 本部门及下级部门数据 |
| all | 全部数据 |

## 前端架构

### 技术栈

- React 18 + TypeScript
- Vite (构建工具)
- TailwindCSS (样式)
- Zustand (状态管理)
- React Router (路由)
- Axios (HTTP 客户端)
- React Markdown (Markdown 渲染)

### 组件结构

```
src/
├── components/
│   ├── layout/          # 布局组件
│   ├── chat/            # 聊天组件
│   └── analysis/        # 分析组件
├── pages/               # 页面组件
├── stores/              # Zustand 状态
├── hooks/               # 自定义 Hooks
├── api/                 # API 客户端
└── types/               # TypeScript 类型
```

## LLM 集成

### 意图检测流程

```
用户输入
    │
    ▼
┌─────────────────┐
│  意图分类器      │
└─────────────────┘
    │
    ├── general_chat ──► 直接 LLM 回复
    │
    └── bio_analysis ──► 分析路由器
                              │
                              ├── volcano_plot
                              ├── go_enrichment
                              └── ...
```

### 支持的分析类型

| 类型 | 工具 | 描述 |
|------|------|------|
| 转录组 | volcano_plot | 火山图 |
| 转录组 | heatmap | 热图 |
| 转录组 | go_enrichment | GO富集 |
| 基因组 | snp_density | SNP密度图 |
| 基因组 | vcf_analysis | VCF分析 |
| 微生物组 | taxonomy_plot | 物种组成图 |

## 安全设计

### 认证流程

1. 用户登录 → 验证密码
2. 生成 JWT Token (access_token + refresh_token)
3. 客户端存储 Token
4. 请求携带 Authorization Header
5. Token 过期时使用 refresh_token 刷新

### 安全措施

- Argon2 密码哈希
- JWT 短期 Token
- CORS 白名单
- SQL 注入防护
- XSS 防护

## 部署架构

### Docker Compose

```yaml
services:
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```