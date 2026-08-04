# M1 阶段说明 — 组织权限 + 多公司预留

| 项 | 内容 |
| --- | --- |
| 阶段 | M1 |
| 状态 | **已完成** |
| 目标 | 登录鉴权、RBAC、默认公司上下文；模型预留多公司 |
| 前置 | M0 完成 |
| 关联文档 | [database.md](./database.md) |

---

## 1. 功能需求

| ID | 需求 | 优先级 | 进度 |
| --- | --- | --- | --- |
| M1-F01 | 用户登录 / 登出，签发 Access + Refresh JWT | P0 | **已完成**（login/refresh/logout/me） |
| M1-F02 | 用户 CRUD、启用/停用 | P0 | **已完成**（列表/创建/详情/PATCH） |
| M1-F03 | 角色、权限点维护；用户绑定角色 | P0 | **已完成** |
| M1-F04 | 接口级鉴权：无 Token 401；无权限 403 | P0 | **已完成**（`require_permissions`） |
| M1-F05 | 公司主数据；用户关联公司；默认公司 | P0 | **已完成** |
| M1-F06 | 请求解析公司上下文（Header `X-Company-Id` 或默认公司） | P0 | **已完成** |
| M1-F07 | 前端登录页；登录后布局；菜单按权限显示 | P0 | **已完成** |
| M1-F08 | 种子数据：管理员、默认公司（本位币 CNY）、基础角色权限 | P0 | **已完成** |
| M1-F09 | 多公司切换 UI / 细粒度按公司授权 | P2（本阶段不做） | 不做 |

---

## 2. 用例（验收对照）

| 用例 | 结果 |
| --- | --- |
| UC-M1-01 管理员登录 | 前端 `/login` + Swagger login 可用 |
| UC-M1-02 维护用户与角色 | 前端用户/角色页 + org API |
| UC-M1-03 公司上下文 | `X-Company-Id`；非法公司 403 |
| UC-M1-04 菜单按权限渲染 | 侧栏按 `hasPermission` 过滤 |

---

## 3. 数据库表

| 表 | 库中状态 |
| --- | --- |
| companies / users / roles / permissions / user_roles / role_permissions / user_companies | **已创建** |

种子：

```bash
cd backend
python -m app.scripts.seed
```

默认账号：`admin` / `admin123`

---

## 4. 已实现接口

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| POST | `/auth/login` | 公开 |
| POST | `/auth/refresh` | 公开（refresh token） |
| POST | `/auth/logout` | 登录用户 |
| GET | `/auth/me` | 登录用户 |
| GET/POST | `/org/companies` | company.read / write |
| GET/PATCH | `/org/companies/{id}` | company.read / write |
| GET/POST | `/org/users` | user.read / write |
| GET/PATCH | `/org/users/{id}` | user.read / write |
| PUT | `/org/users/{id}/roles` | user.write |
| GET/POST | `/org/roles` | role.read / write |
| PUT | `/org/roles/{id}/permissions` | role.write |
| GET | `/org/permissions` | role.read |

统一 Header：

- `Authorization: Bearer <access_token>`
- `X-Company-Id: <company_id>`（可选）

---

## 5. 前端页面

- `/login` 登录页  
- 控制台布局：当前公司、用户、退出  
- `/companies` `/users` `/roles` 简表管理  
- 路由守卫 + 按权限菜单  

---

## 6. 验收标准

| 标准 | 结果 |
| --- | --- |
| 管理员可登录；错误密码失败 | 通过（pytest） |
| 无 Token 访问受保护接口 401 | 通过 |
| 无权限 / 非法公司 403 | 通过 |
| 默认公司上下文生效 | 通过 |
| 种子幂等 | 通过 |

后端测试：`pytest` → 11 passed。

---

## 7. 关键代码位置

- 鉴权依赖：`backend/app/api/deps.py`  
- 认证路由：`backend/app/api/routes/auth.py`  
- 组织路由：`backend/app/api/routes/org.py`  
- 业务服务：`backend/app/modules/org/services.py`  
- 前端鉴权：`frontend/src/stores/auth.ts`、`frontend/src/router/index.ts`  

---

## 8. 下一阶段

进入 **[M2](./m2_status.md)**：主数据 + 库存核心。
