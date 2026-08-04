# M1 阶段说明 — 组织权限 + 多公司预留

| 项 | 内容 |
| --- | --- |
| 阶段 | M1 |
| 状态 | **进行中**（表 + 种子 + login/me 已完成；组织 CRUD / 前端登录未做） |
| 目标 | 登录鉴权、RBAC、默认公司上下文；模型预留多公司 |
| 前置 | M0 完成 |
| 关联文档 | [database.md](./database.md) |

---

## 1. 功能需求

| ID | 需求 | 优先级 | 进度 |
| --- | --- | --- | --- |
| M1-F01 | 用户登录 / 登出，签发 Access + Refresh JWT | P0 | 登录已完成；refresh/logout 未做 |
| M1-F02 | 用户 CRUD、启用/停用 | P0 | 未做 |
| M1-F03 | 角色、权限点维护；用户绑定角色 | P0 | 未做（种子已预置） |
| M1-F04 | 接口级鉴权：无 Token 401；无权限 403 | P0 | Token 鉴权已有；权限点校验未做 |
| M1-F05 | 公司主数据；用户关联公司；默认公司 | P0 | 种子已有；公司 API 未做 |
| M1-F06 | 请求解析公司上下文（Header `X-Company-Id` 或默认公司） | P0 | 未做（me 返回默认 company_id） |
| M1-F07 | 前端登录页；登录后布局；菜单按权限显示 | P0 | 未做 |
| M1-F08 | 种子数据：管理员、默认公司（本位币 CNY）、基础角色权限 | P0 | **已完成** |
| M1-F09 | 多公司切换 UI / 细粒度按公司授权 | P2（本阶段不做） | 不做 |

---

## 2. 用例

### UC-M1-01 管理员登录

1. 打开登录页，输入种子管理员账号  
2. 成功后获得 Token，进入控制台  
3. 无 Token 访问受保护接口返回 401  

### UC-M1-02 维护用户与角色

1. 管理员创建用户并绑定「采购员」角色  
2. 该用户仅能访问采购相关权限接口  
3. 访问无权限接口返回 403  

### UC-M1-03 公司上下文

1. 用户属于默认公司 A  
2. 请求不带 Header 时使用默认公司  
3. 带合法 `X-Company-Id` 且用户有权时切换上下文；非法则拒绝  

### UC-M1-04 菜单按权限渲染

1. 不同角色登录看到不同侧栏菜单  
2. 直接访问无权限前端路由被拦截或提示  

---

## 3. 需要用到的数据库表

| 表 | 说明 | 本阶段创建 | 库中状态 |
| --- | --- | --- | --- |
| `companies` | 公司 | 是 | **已创建** |
| `users` | 用户 | 是 | **已创建** |
| `roles` | 角色 | 是 | **已创建** |
| `permissions` | 权限点 | 是 | **已创建** |
| `user_roles` | 用户-角色 | 是 | **已创建** |
| `role_permissions` | 角色-权限 | 是 | **已创建** |
| `user_companies` | 用户-公司 | 是 | **已创建** |

迁移：`20260805_0002_m1_org_rbac`；模型：`backend/app/modules/org/models.py`；审计：`AuditMixin`。

字段详见 [database.md §3.2](./database.md)。

### 种子数据用法

```bash
cd backend
# conda env: cursor-erp-demo
python -m app.scripts.seed
```

默认账号：`admin` / `admin123`（仅开发环境）。

---

## 4. 需要编写的接口

前缀：`/api/v1`  
认证：除登录/刷新外，均需 `Authorization: Bearer <access_token>`  
可选 Header：`X-Company-Id`

| 方法 | 路径 | 说明 | 权限建议 |
| --- | --- | --- | --- |
| POST | `/auth/login` | 登录，返回 access/refresh | 公开 |
| POST | `/auth/refresh` | 刷新 Token | 公开（凭 refresh） |
| POST | `/auth/logout` | 登出（可选黑名单/废弃 refresh） | 登录用户 |
| GET | `/auth/me` | 当前用户、角色、权限、公司列表 | 登录用户 |
| GET/POST | `/org/companies` | 公司列表/创建 | `org.company.*` |
| GET/PATCH | `/org/companies/{id}` | 公司详情/更新 | `org.company.*` |
| GET/POST | `/org/users` | 用户列表/创建 | `org.user.*` |
| GET/PATCH | `/org/users/{id}` | 用户详情/更新/停用 | `org.user.*` |
| PUT | `/org/users/{id}/roles` | 绑定角色 | `org.user.*` |
| GET/POST | `/org/roles` | 角色列表/创建 | `org.role.*` |
| PUT | `/org/roles/{id}/permissions` | 绑定权限 | `org.role.*` |
| GET | `/org/permissions` | 权限点列表 | `org.role.read` |

---

## 5. 简要接口文档

### 5.1 `POST /api/v1/auth/login`

**请求**

```json
{ "username": "admin", "password": "admin123" }
```

**响应 data**

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "display_name": "系统管理员",
    "roles": ["admin"],
    "permissions": ["*"],
    "companies": [{ "id": 1, "code": "DEFAULT", "name": "演示公司", "is_default": true }]
  }
}
```

### 5.2 `GET /api/v1/auth/me`

**响应 data：** 同登录中的 `user` 结构（可含当前 `company_id`）。

### 5.3 `GET /api/v1/org/users?page=1&page_size=20`

**响应 data**

```json
{
  "items": [
    {
      "id": 2,
      "username": "buyer01",
      "display_name": "采购员甲",
      "status": "active",
      "roles": ["buyer"]
    }
  ],
  "meta": { "page": 1, "page_size": 20, "total": 1 }
}
```

### 5.4 错误码约定（本阶段）

| HTTP | code | 含义 |
| --- | --- | --- |
| 401 | 40100 | 未认证 / Token 无效 |
| 403 | 40300 | 无权限 / 无公司访问权 |
| 404 | 40400 | 资源不存在 |
| 422 | 42200 | 参数校验失败 |

---

## 6. 前端页面

- 登录页  
- 控制台布局（复用/强化 M0 Layout）  
- 用户管理、角色管理（简表）  
- 当前公司展示（切换 UI 可 P2）  

---

## 7. 验收标准

- 管理员可登录；错误密码失败  
- 无 Token 访问受保护接口 401  
- 无权限接口 403  
- 默认公司上下文生效；列表查询带 `company_id` 过滤（后续业务表沿用）  
- 种子数据可重复执行或幂等初始化脚本  

---

## 8. 下一阶段

完成后进入 **[M2](./m2_status.md)**：主数据 + 库存核心。
