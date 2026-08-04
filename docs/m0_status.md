# M0 阶段说明 — 工程脚手架

| 项 | 内容 |
| --- | --- |
| 阶段 | M0 |
| 状态 | **已完成** |
| 目标 | 前后端可启动、基础设施就绪、本地可联调 |
| 依赖环境 | Conda `cursor-erp-demo`（Python 3.13）、MySQL `erp_demo`、Node.js |
| 关联文档 | [database.md](./database.md)、[README.md](../README.md) |

---

## 1. 功能需求

| ID | 需求 | 优先级 | 完成 |
| --- | --- | --- | --- |
| M0-F01 | 后端 FastAPI 工程可启动，提供 OpenAPI `/docs` | P0 | 是 |
| M0-F02 | 统一响应体、业务异常、校验异常、HTTP 异常处理 | P0 | 是 |
| M0-F03 | CORS、日志、环境配置（`.env`） | P0 | 是 |
| M0-F04 | SQLAlchemy Engine/Session + Alembic 基线迁移 | P0 | 是 |
| M0-F05 | 健康检查接口（含 MySQL 连通性） | P0 | 是 |
| M0-F06 | 前端 Vue3 + Vite + TS + Router 壳页面 | P0 | 是 |
| M0-F07 | 前端经代理调用后端健康检查 | P0 | 是 |
| M0-F08 | 项目文档与启动说明 | P0 | 是 |

**明确不做（留给后续阶段）：** 登录、业务 CRUD、业务表、JWT、菜单权限。

---

## 2. 用例

### UC-M0-01 启动后端并查看 API 文档

1. 使用 Conda 环境启动 uvicorn  
2. 浏览器打开 `http://127.0.0.1:8000/docs`  
3. 可见健康检查接口并可 Try it out  

### UC-M0-02 健康检查含数据库状态

1. 请求 `GET /api/v1/health`  
2. 返回 `status=healthy`，`database.name=erp_demo`  

### UC-M0-03 前端壳访问后端

1. 启动 Vite 开发服  
2. 打开 `http://127.0.0.1:5173/health`  
3. 页面展示应用与数据库状态  

---

## 3. 涉及数据库表

| 表 | 用途 | 是否已创建 |
| --- | --- | --- |
| `alembic_version` | 迁移版本 | **是** |

业务表：无（基线迁移为空）。详见 [database.md](./database.md)。

---

## 4. 本阶段实际交付（代码 Review 澄清）

### 4.1 后端已有

| 路径 | 作用 |
| --- | --- |
| `backend/app/main.py` | FastAPI 入口、CORS、全局异常、根路由 |
| `backend/app/core/config.py` | pydantic-settings 配置 |
| `backend/app/core/response.py` | 统一 `code/message/data` |
| `backend/app/core/exceptions.py` | AppError / 401 / 403 / 404 |
| `backend/app/core/logging.py` | 日志初始化 |
| `backend/app/db/base.py` | DeclarativeBase |
| `backend/app/db/session.py` | Engine / Session / `get_db` |
| `backend/app/api/router.py` | `/api/v1` 路由聚合 |
| `backend/app/api/routes/health.py` | 健康检查 + DB 探活 |
| `backend/alembic/` | 迁移框架 + `20260804_0001` baseline |
| `backend/tests/test_health.py` | 健康检查测试 |
| `backend/.env` | MySQL 连接等本地配置 |

### 4.2 前端已有

| 路径 | 作用 |
| --- | --- |
| `frontend/src/main.ts` + `router` | Vue + Vue Router |
| `frontend/src/layouts/AppLayout.vue` | 侧栏布局壳 |
| `frontend/src/pages/HomePage.vue` | 首页说明 |
| `frontend/src/pages/HealthPage.vue` | 健康检查页 |
| `frontend/src/api/client.ts` | `fetch` 封装 |
| `frontend/vite.config.ts` | `/api` 代理到 `:8000` |

### 4.3 环境与选型结论

- Python 运行环境：**Conda `cursor-erp-demo`**（非系统 Python 3.14、非 `.venv`）  
- 前端：**Vue 3**（非 React）  
- 数据库：**MySQL 8** 库 `erp_demo`  
- 依赖管理：后端 `pip + requirements.txt`；前端 npm  

---

## 5. 接口清单与简要文档

统一响应：

```json
{ "code": 0, "message": "ok", "data": {} }
```

### 5.1 `GET /`

| 项 | 说明 |
| --- | --- |
| 认证 | 无 |
| 说明 | 服务元信息 |
| 响应 data | `name`, `docs`, `health` |

### 5.2 `GET /api/v1/health`

| 项 | 说明 |
| --- | --- |
| 认证 | 无 |
| 说明 | 应用 + MySQL 健康状态 |
| 成功示例 | 见下 |

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "healthy",
    "app": "Cursor ERP Demo",
    "env": "development",
    "database": {
      "status": "ok",
      "name": "erp_demo",
      "version": "8.4.6"
    }
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `status` | `healthy` 或 `degraded`（DB 失败时） |
| `database.status` | `ok` 或 `error: ExceptionName` |

交互文档：运行后端后访问 http://127.0.0.1:8000/docs

---

## 6. 验收标准与结果

| 标准 | 结果 |
| --- | --- |
| 后端可启动，`/docs` 可访问 | 通过 |
| `/api/v1/health` 返回 healthy 且连上 MySQL | 通过 |
| Alembic baseline 已 upgrade | 通过（`20260804_0001`） |
| 前端可 build / 可 `npm run dev` | 通过 |
| `pytest` 健康检查通过 | 通过（2 passed） |

---

## 7. 已知问题（环境，非业务缺陷）

| 问题 | 处理建议 |
| --- | --- |
| PowerShell 下 `conda activate` 可能未生效 | 用 `conda run -n cursor-erp-demo python -m uvicorn ...` |
| PowerShell 禁止 `npm.ps1` | 用 `npm.cmd run dev` 或放宽 ExecutionPolicy |
| IDE 提示 `@vue/tsconfig/... not found` | 多为 TS Server 未识别 `frontend/node_modules`，重启 TS Server |

---

## 8. 下一阶段入口

完成后进入 **[M1](./m1_status.md)**：组织、用户、角色权限、JWT、公司上下文。
