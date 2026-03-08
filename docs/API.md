# BioCloud API 文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json`

## 认证

### 登录

```http
POST /auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**响应**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 注册

```http
POST /auth/register
Content-Type: application/json

{
  "username": "string",
  "password": "string",
  "name": "string",
  "email": "string (optional)"
}
```

### 刷新Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "string"
}
```

### 获取当前用户

```http
GET /auth/me
Authorization: Bearer <access_token>
```

## 用户管理

### 获取用户列表

```http
GET /users?page=1&page_size=20
Authorization: Bearer <access_token>
```

### 创建用户

```http
POST /users
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "string",
  "password": "string",
  "name": "string",
  "email": "string",
  "dept_id": 1,
  "role_ids": [1, 2]
}
```

### 更新用户

```http
PUT /users/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "string",
  "email": "string",
  "dept_id": 1
}
```

### 删除用户

```http
DELETE /users/{id}
Authorization: Bearer <access_token>
```

## 部门管理

### 获取部门树

```http
GET /departments
Authorization: Bearer <access_token>
```

**响应**:

```json
[
  {
    "id": 1,
    "name": "总部",
    "parent_id": null,
    "dept_path": ".1.",
    "children": [
      {
        "id": 2,
        "name": "研发部",
        "parent_id": 1,
        "dept_path": ".1.2.",
        "children": []
      }
    ]
  }
]
```

### 创建部门

```http
POST /departments
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "string",
  "parent_id": 1,
  "leader_user_id": 1,
  "order_num": 0
}
```

## 角色管理

### 获取角色列表

```http
GET /roles
Authorization: Bearer <access_token>
```

### 创建角色

```http
POST /roles
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "string",
  "role_key": "string",
  "data_scope_type": "self",
  "permission_ids": [1, 2, 3]
}
```

## 对话

### 获取对话列表

```http
GET /conversations
Authorization: Bearer <access_token>
```

### 创建对话

```http
POST /conversations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "新对话",
  "model": "claude"
}
```

### 获取对话详情

```http
GET /conversations/{id}
Authorization: Bearer <access_token>
```

### 发送消息 (SSE流式)

```http
POST /conversations/{id}/messages
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "请帮我分析这个差异表达数据"
}
```

**响应** (Server-Sent Events):

```
data: {"content": "我"}
data: {"content": "来"}
data: {"content": "帮"}
data: {"content": "你"}
data: [DONE]
```

### 删除对话

```http
DELETE /conversations/{id}
Authorization: Bearer <access_token>
```

## 分析

### 获取分析历史

```http
GET /analyses
Authorization: Bearer <access_token>
```

### 创建分析任务

```http
POST /analyses
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "analysis_type": "volcano_plot",
  "input_file_id": 1,
  "parameters": {
    "fc_threshold": 1.0,
    "p_threshold": 0.05
  }
}
```

### 获取分析结果

```http
GET /analyses/{id}/result
Authorization: Bearer <access_token>
```

## 文件上传

### 上传文件

```http
POST /files/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary>
```

## 错误码

| 状态码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 验证错误 |
| 500 | 服务器错误 |

## 权限标识

| 权限 | 描述 |
|------|------|
| user:view | 查看用户 |
| user:create | 创建用户 |
| user:update | 更新用户 |
| user:delete | 删除用户 |
| dept:view | 查看部门 |
| dept:create | 创建部门 |
| role:view | 查看角色 |
| role:create | 创建角色 |
| analysis:run | 运行分析 |