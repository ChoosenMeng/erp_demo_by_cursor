# Cursor ERP Demo

基于 Python 的轻量级 ERP 演示系统。面向中小型企业常见业务场景，优先交付可运行、可演示的 MVP，同时在数据模型与架构上预留**多公司**、**多币种**扩展能力。

---

## 1. 文档说明

| 项 | 说明 |
| --- | --- |
| 文档类型 | 需求文档 + 开发计划 |
| 目标读者 | 开发者、产品评审、演示相关方 |
| 当前阶段 | M0 脚手架已搭建（可本地启动） |
| 版本 | v0.1 |

---

## 2. 产品定位

### 2.1 目标

搭建一套可本地运行的 ERP Demo，覆盖「主数据 → 采销库存 → 简版财务 → 仪表盘」闭环，用于：

- 验证业务链路与领域模型是否合理
- 作为后续扩展（多公司、多币种、生产/MRP 等）的基线
- 支持功能演示与二次开发

### 2.2 非目标（本期不做）

- 完整生产制造 / MRP / APS
- 复杂税务引擎、多账套并行结账
- 移动端原生 App
- 高可用集群与多租户 SaaS 计费
- 与外部电商/银行的深度对接

---

## 3. 技术选型

### 3.1 架构原则

- **前后端分离**：后端提供 REST API，前端独立工程
- **领域清晰**：按模块划分（组织权限、主数据、采购、销售、库存、财务）
- **可扩展**：MVP 单公司、单本位币运行；模型层预留 `company_id`、`currency_code` 等字段与服务边界
- **可演示**：提供种子数据与一键启动说明

### 3.2 推荐技术栈

| 层级 | 技术 | 说明 |
| --- | --- | --- |
| 后端 | Python 3.13、FastAPI、Pydantic v2 | API、校验、依赖注入 |
| 运行环境 | Conda：`cursor-erp-demo` | 见根目录 `environment.yml` |
| ORM / 迁移 | SQLAlchemy 2.x、Alembic | 模型与版本化迁移 |
| 数据库 | MySQL 8（库名 `erp_demo`） | 本机已验证；驱动 PyMySQL |
| 认证 | JWT（Access + Refresh） | 无状态 API，便于前后端分离（M1） |
| 前端 | Vue 3 + TypeScript + Vite + Vue Router | 管理后台 SPA |
| 权限 | RBAC（角色 + 权限点 + 菜单） | 接口级鉴权 + 前端菜单控制（M1） |
| 工具 | pip + requirements.txt、Ruff、pytest、httpx | 依赖与质量保障 |
| 容器（后期） | Docker Compose | API + DB + 前端静态资源 |

### 3.3 当前仓库结构

```text
cursor-erp-demo/
├── README.md                          # 需求 + 选型 + 启动说明（本文）
├── environment.yml                    # Conda 环境：cursor-erp-demo
├── .gitignore
│
├── docs/                              # 阶段文档与数据字典
│   ├── database.md                    # 全库表/字段/是否已创建
│   ├── m0_status.md … m5_status.md    # 各阶段需求、用例、接口
│
├── backend/                           # FastAPI 后端（≈ Spring Boot 工程）
│   ├── .env / .env.example            # 本地配置（密钥、DATABASE_URL）
│   ├── requirements.txt               # pip 依赖（≈ pom.xml / build.gradle）
│   ├── alembic.ini                    # Alembic 配置
│   ├── alembic/
│   │   ├── env.py                     # 迁移运行时（加载 metadata）
│   │   └── versions/
│   │       ├── 20260804_0001_baseline.py
│   │       └── 20260805_0002_m1_org_rbac.py
│   ├── tests/
│   │   ├── test_health.py
│   │   └── test_auth.py
│   └── app/                           # 应用包（≈ src/main/java/...）
│       ├── main.py                    # 应用入口：创建 FastAPI、挂中间件/路由
│       ├── core/                      # 横切基础设施（≈ common / config）
│       │   ├── config.py              # 配置（≈ @ConfigurationProperties）
│       │   ├── security.py            # 密码哈希、JWT
│       │   ├── exceptions.py          # 业务异常
│       │   ├── response.py            # 统一响应体
│       │   └── logging.py             # 日志初始化
│       ├── db/                        # 持久化基础设施（≈ JPA 配置）
│       │   ├── base.py                # DeclarativeBase
│       │   ├── session.py             # Engine / Session / get_db
│       │   └── models.py              # 汇总 import 所有 ORM（给 Alembic 用）
│       ├── api/                       # 接入层（≈ Controller + 部分 Filter）
│       │   ├── router.py              # 聚合 /api/v1 路由
│       │   ├── deps.py                # 依赖注入：DB、当前用户
│       │   └── routes/
│       │       ├── health.py          # GET /health
│       │       └── auth.py            # POST /login、GET /me
│       ├── modules/                   # 业务域（≈ domain packages）
│       │   └── org/                   # 组织权限域（后续还有 master/purchase…）
│       │       ├── models.py          # ORM 实体（≈ @Entity）
│       │       ├── schemas.py         # 请求/响应 DTO（≈ DTO / VO）
│       │       ├── services.py        # 业务逻辑（≈ @Service）
│       │       └── seed.py            # 种子数据逻辑
│       ├── shared/                    # 跨模块复用
│       │   └── mixins.py              # AuditMixin 等
│       └── scripts/                   # 运维脚本入口
│           └── seed.py                # python -m app.scripts.seed
│
└── frontend/                          # Vue3 前端（独立 SPA）
    ├── package.json
    ├── vite.config.ts                 # 开发代理 /api → :8000
    ├── index.html
    └── src/
        ├── main.ts                    # 前端入口
        ├── App.vue
        ├── style.css
        ├── router/index.ts            # 路由（≈ Vue Router）
        ├── api/client.ts              # HTTP 封装
        ├── layouts/AppLayout.vue      # 布局壳
        └── pages/
            ├── HomePage.vue
            └── HealthPage.vue
```

### 3.4 后端分层说明（对照 Spring Boot）

如果你熟悉 **Spring Boot 经典分层**，可以把本项目大致映射如下：

| 本项目（FastAPI） | Spring Boot 常见对应 | 主要职责 |
| --- | --- | --- |
| `app/main.py` | `Application.java` + 部分 `WebMvcConfig` | 启动应用；注册 CORS、全局异常、挂载路由 |
| `app/api/routes/*.py` | `@RestController` | 只处理 HTTP：收参、调 service、返回统一 JSON |
| `app/api/deps.py` | `HandlerMethodArgumentResolver` / Security 上下文 | 依赖注入：拿 DB Session、解析 JWT 得到当前用户 |
| `app/modules/*/schemas.py` | DTO / Request/Response VO | 入参校验与出参形状（Pydantic ≈ Bean Validation + 序列化） |
| `app/modules/*/services.py` | `@Service` | **业务逻辑**写在这里，不要堆在路由里 |
| `app/modules/*/models.py` | `@Entity` + Repository 实体 | 表结构映射（SQLAlchemy ORM） |
| `app/db/session.py` | `DataSource` / `EntityManager` | 创建连接引擎、提供请求级 Session |
| `app/core/*` | `config`、`Security`、统一异常/响应 | 配置、安全、日志、公共异常与响应格式 |
| `app/shared/*` | `common` 工具/基类 | 多模块共用（如审计字段 Mixin） |
| `alembic/` | Flyway / Liquibase | **数据库结构版本迁移**（不是数据备份） |
| `app/scripts/` | `CommandLineRunner` / 运维脚本 | 种子数据等一次性/可重复维护任务 |
| `tests/` | `src/test/java` | pytest 接口/单元测试 |
| `frontend/` | 独立前端工程（非 Thymeleaf） | Vue SPA，通过 HTTP 调后端 API |

**一次请求怎么走（对照理解）：**

```text
浏览器 / Swagger
    → api/routes/auth.py          # Controller：收 LoginRequest
        → deps.get_db()           # 注入 Session（≈ 打开 EntityManager）
        → modules/org/services.py # Service：校验密码、发 JWT、拼 UserMe
            → modules/org/models.py + db/session
            → MySQL erp_demo
        ← 统一 ok({...})          # response.py（≈ 统一 Result 包装）
```

**和 Spring 的几个关键差异（第一次接触 Python 时记住即可）：**

1. **没有强制的 Interface + Impl**：Python 常直接写 `services.py` 函数/类，需要抽象时再抽。  
2. **依赖注入更轻**：FastAPI 的 `Depends(...)` ≈ Spring 注入参数，但范围主要是「一次请求」。  
3. **DTO 用 Pydantic，实体用 SQLAlchemy**：不要把 ORM 模型直接当对外 API 模型（和「Entity 不要直接暴露」同一原则）。  
4. **按业务域分包 `modules/org`**：类似按 bounded context 拆 package，而不是所有 Entity 扔一个 `model` 包。  
5. **Alembic ≈ Flyway**：改表请写 migration，再 `alembic upgrade head`。

### 3.5 本地启动

**前置：** MySQL 已运行，库 `erp_demo` 已创建；账号密码见 `backend/.env`。

```bash
# 1) 激活 Conda 环境
conda activate cursor-erp-demo

# 2) 后端（在 backend 目录）
cd backend
pip install -r requirements.txt   # 仅首次或依赖变更时
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 3) 前端（新开终端，在 frontend 目录）
cd frontend
npm install                       # 仅首次或依赖变更时
npm run dev
```

- API 文档：http://127.0.0.1:8000/docs  
- 健康检查：http://127.0.0.1:8000/api/v1/health  
- 前端：http://127.0.0.1:5173  

重建 Conda 环境（可选）：

```bash
conda env create -f environment.yml
# 或已存在时：conda env update -f environment.yml --prune
```

---

## 4. 功能需求（MVP）

### 4.1 组织与权限

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 登录 / 登出 | 用户名密码登录，签发 JWT | P0 |
| 用户管理 | CRUD、启用/停用 | P0 |
| 角色与权限 | 角色绑定权限点；用户绑定角色 | P0 |
| 菜单权限 | 按权限控制侧边栏与路由 | P0 |
| 当前公司上下文 | MVP 默认一家公司；请求可携带 `company_id` | P0（扩展预留） |
| 多公司切换 / 数据隔离 | 用户可属多公司、按公司过滤数据 | P2（扩展） |

**默认角色（种子数据）建议：**

- 系统管理员
- 业务员（销售）
- 采购员
- 仓管员
- 财务

### 4.2 主数据

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 客户 | 编码、名称、联系人、信用相关字段（简） | P0 |
| 供应商 | 编码、名称、联系人 | P0 |
| 物料/产品 | 编码、名称、规格、单位、类型（成品/原材料） | P0 |
| 仓库 | 仓库编码、名称；默认仓 | P0 |
| 币种主数据 | 币种代码、名称、符号；本位币配置 | P1（模型 P0 预留） |
| 汇率 | 日期汇率表（对本位币） | P2（扩展） |

### 4.3 采购

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 采购订单 | 供应商、明细行、数量、单价、币种、税率（简） | P0 |
| 订单状态 | 草稿 → 已确认 → 部分入库 / 已完成 → 关闭 | P0 |
| 采购入库 | 依据采购订单生成入库单，更新库存 | P0 |
| 询价单 | 多供应商比价 | P2 |

### 4.4 销售

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 销售订单 | 客户、明细行、数量、单价、币种 | P0 |
| 订单状态 | 草稿 → 已确认 → 部分出库 / 已完成 → 关闭 | P0 |
| 销售出库 | 依据销售订单生成出库单，扣减库存 | P0 |
| 报价单 | 报价转订单 | P2 |

### 4.5 库存

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 库存余额 | 按公司 + 仓库 + 物料查询可用量 | P0 |
| 出入库流水 | 记录类型、单据号、数量、方向 | P0 |
| 库存校验 | 出库时可用量不足则拒绝 | P0 |
| 盘点 / 调拨 | 盘盈盘亏、仓间调拨 | P2 |

### 4.6 财务（简版）

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 应付 | 采购确认/入库后生成应付（简化规则） | P1 |
| 应收 | 销售确认/出库后生成应收（简化规则） | P1 |
| 收付款登记 | 登记核销状态（简） | P1 |
| 凭证 / 总账 | 完整会计凭证体系 | 不做（后续） |

### 4.7 仪表盘

| 功能 | 描述 | 优先级 |
| --- | --- | --- |
| 关键指标 | 今日/本月销售额、采购额、库存 SKU 数、待办订单数 | P1 |
| 简单图表 | 近 7/30 日销售趋势 | P1 |

---

## 5. 可扩展性设计（多公司 / 多币种）

MVP **运行时**以「单公司 + 单本位币」为主，避免复杂度阻塞交付；但在设计与实现时遵守以下约定，避免日后推倒重来。

### 5.1 多公司（Multi-Company）

**原则：**

1. 业务主表普遍包含 `company_id`（或等价组织维度），查询默认带公司过滤。
2. 用户与公司为多对多（`user_company`）；MVP 种子数据只挂一家公司。
3. API 通过 Header（如 `X-Company-Id`）或用户默认公司解析当前上下文；服务层统一注入，禁止前端随意跨公司写数据。
4. 编号规则、仓库、物料是否跨公司共享：MVP 默认**公司内隔离**；共享策略留配置位。
5. 权限可按公司裁剪（后期）；MVP 先做全局角色权限。

**建议表字段（示例）：**

```text
companies(id, code, name, base_currency_code, status, ...)
users(...)
user_companies(user_id, company_id, is_default)
# 业务表
sales_orders(id, company_id, customer_id, currency_code, ...)
```

### 5.2 多币种（Multi-Currency）

**原则：**

1. 金额类单据保留：`currency_code`、`exchange_rate`、`amount`（原币）、`base_amount`（本位币）。
2. 公司配置 `base_currency_code`；MVP 汇率固定为 `1.0`，币种与本位币一致。
3. 公共服务 `CurrencyService` / `Money` 值对象：换算、舍入规则集中处理，业务模块不散落魔法数。
4. 库存数量与币种解耦；金额在订单/财务层处理。
5. 汇率表、历史汇率、重估留作 P2，接口与表结构先预留。

**建议字段（单据头/行）：**

```text
currency_code        # ISO 4217，如 CNY / USD
exchange_rate        # 相对本位币
amount / tax_amount  # 原币
base_amount          # 本位币折算
```

### 5.3 扩展检查清单（编码时自检）

- [ ] 新建业务表是否包含 `company_id`
- [ ] 列表/详情查询是否强制公司作用域
- [ ] 金额字段是否区分原币与本位币
- [ ] 种子数据是否可增加第二公司而不改表结构
- [ ] 单元测试是否覆盖「无公司上下文拒绝访问」

---

## 6. 非功能需求

| 类别 | 要求 |
| --- | --- |
| 性能 | Demo 级：单机百级并发足够；列表分页默认 20 |
| 安全 | 密码哈希（bcrypt/argon2）；JWT 过期；接口鉴权；基础输入校验 |
| 审计 | 关键表记录 `created_at/by`、`updated_at/by`；重要状态变更可记日志（简） |
| 可用性 | 中文界面；表单校验提示明确；关键错误码与消息 |
| 可测性 | 核心领域（库存扣减、订单状态机）有 pytest |
| 可维护性 | 模块边界清晰；OpenAPI 自动文档（FastAPI `/docs`） |

---

## 7. 关键业务流程（MVP）

### 7.1 采购入库

```text
创建采购订单(草稿)
  → 确认订单
  → 创建入库单(关联 PO 行)
  → 过账：增加库存流水 + 更新库存余额
  → (P1) 生成应付
```

### 7.2 销售出库

```text
创建销售订单(草稿)
  → 确认订单
  → 创建出库单(关联 SO 行，校验库存)
  → 过账：扣减库存 + 流水
  → (P1) 生成应收
```

### 7.3 状态机（订单）

```text
draft → confirmed → partial / completed → closed
         ↘ cancelled（仅未执行出入库时可取消）
```

---

## 8. 接口与前端范围（概要）

### 8.1 后端 API 分组（示例前缀）

| 前缀 | 模块 |
| --- | --- |
| `/api/v1/auth` | 登录、刷新、当前用户 |
| `/api/v1/org` | 公司、用户、角色、权限 |
| `/api/v1/master` | 客户、供应商、物料、仓库、币种 |
| `/api/v1/purchase` | 采购订单、入库 |
| `/api/v1/sales` | 销售订单、出库 |
| `/api/v1/inventory` | 库存余额、流水 |
| `/api/v1/finance` | 应收应付、收付款 |
| `/api/v1/dashboard` | 汇总指标 |

统一约定：

- 分页：`page`、`page_size`
- 响应：`{ "data": ..., "message": "...", "code": 0 }`
- 错误：HTTP 状态码 + 业务 `code`
- 公司上下文：`X-Company-Id`（可选，缺省用用户默认公司）

### 8.2 前端页面（MVP）

- 登录
- 仪表盘
- 用户 / 角色
- 客户 / 供应商 / 物料 / 仓库
- 采购订单列表与详情、入库
- 销售订单列表与详情、出库
- 库存查询与流水
- 应收应付列表（P1）

---

## 9. 开发计划

### 阶段总览

| 阶段 | 名称 | 目标产出 | 预估工期 |
| --- | --- | --- | --- |
| M0 | 工程脚手架 | 前后端可启动、CI/本地规范 | 2–3 天 |
| M1 | 组织权限 + 多公司预留 | 登录、RBAC、公司上下文 | 3–5 天 |
| M2 | 主数据 + 库存核心 | CRUD + 库存余额/流水服务 | 4–6 天 |
| M3 | 采销闭环 | PO/SO + 入出库过账 | 5–7 天 |
| M4 | 财务简版 + 仪表盘 | 应收应付、指标页 | 3–5 天 |
| M5 | 打磨与演示 | 种子数据、文档、缺陷收敛 | 2–3 天 |

> 工期为单人全职粗估，可按并行与范围裁剪调整。

### M0 — 工程脚手架

- [x] 初始化 `backend`（FastAPI、配置、健康检查含 MySQL）
- [x] 初始化 `frontend`（Vite + Vue3 + TS + 路由壳）
- [x] SQLAlchemy + Alembic 基线（空迁移 `20260804_0001`）
- [x] 统一响应/异常处理、日志、CORS
- [x] README 补充启动方式；Conda 环境 `cursor-erp-demo`

### M1 — 组织与权限（含扩展点）

- [ ] `companies`、`users`、`roles`、`permissions`、关联表
- [ ] 注册（可选）/ 登录 / JWT
- [ ] 权限依赖注入与路由保护
- [ ] 公司上下文中间件（`company_id`）
- [ ] 前端：登录页、布局、菜单按权限渲染
- [ ] 种子：管理员 + 默认公司（本位币 CNY）

### M2 — 主数据与库存

- [ ] 客户、供应商、物料、仓库 API + 页面
- [ ] 币种主数据（至少 CNY）；金额公共类型
- [ ] 库存余额表、出入库流水、库存服务（入/出/查）
- [ ] 并发场景：出库库存不足事务回滚（测试覆盖）

### M3 — 采购 / 销售闭环

- [ ] 采购订单 CRUD + 状态流转
- [ ] 采购入库过账 → 库存增加
- [ ] 销售订单 CRUD + 状态流转
- [ ] 销售出库过账 → 库存扣减
- [ ] 单据编号规则（按公司可配置预留）
- [ ] 前端列表/详情/确认/出入库操作流

### M4 — 财务简版与仪表盘

- [ ] 确认/出入库后生成应收应付（规则写清并单测）
- [ ] 收付款登记与状态
- [ ] 仪表盘 API + 前端图表
- [ ] 原币/本位币字段在财务单据落齐（汇率 MVP=1）

### M5 — 打磨与演示

- [ ] 演示用种子数据（第二公司可选开关，验证模型扩展性）
- [ ] OpenAPI 与模块说明
- [ ] 基础 E2E 或关键 API 集成测试
- [ ] Docker Compose（可选）
- [ ] 已知问题列表与下一期 backlog（多公司切换 UI、汇率、盘点等）

---

## 10. 里程碑验收标准

| 里程碑 | 验收标准 |
| --- | --- |
| M1 | 管理员可登录；无权限接口返回 403；默认公司上下文生效 |
| M2 | 可维护主数据；手工或服务层完成入库后库存正确 |
| M3 | 从采购入库到销售出库全流程可在 UI 走通；库存与订单状态一致 |
| M4 | 产生应收应付并可查询；仪表盘展示真实汇总 |
| M5 | 新人按文档 15 分钟内启动并完成一遍演示脚本 |

---

## 11. 风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| 范围蔓延（上生产/MRP） | 延期 | 严格 P0/P1；扩展进 backlog |
| 库存并发与超卖 | 数据错误 | DB 事务 + 行锁/乐观锁；单测 |
| 过早做多公司 UI | 拖慢 MVP | 仅模型与上下文预留，UI 后期 |
| 前后端契约不一致 | 联调成本 | 以 OpenAPI 为契约；尽早联调 |
| 财务规则争议 | 返工 | 简版规则文档化，不做完整总账 |

---

## 12. 下一期 Backlog（非 MVP）

- 多公司切换 UI 与细粒度数据隔离审计
- 汇率维护、外币重估
- 询价 / 报价
- 盘点、调拨、安全库存预警
- 生产工单 / 简易 MRP
- 审批流
- 导入导出（Excel）
- 操作审计报表、打印模板

---

## 13. 当前状态与下一步

**当前状态：M0 已完工并验收通过。**

| 验收项 | 结果 |
| --- | --- |
| Conda 环境 `cursor-erp-demo` | Python 3.13.14 @ `E:\conda\conda_envs\cursor-erp-demo` |
| 后端启动 / 健康检查 | `/api/v1/health` 返回 healthy，MySQL `erp_demo` 8.4.6 |
| Alembic | `20260804_0001` baseline 已 upgrade |
| 前端构建 | `npm run build` 通过 |
| 测试 | `pytest` 2 passed |

**建议下一步（需你确认后再执行）：M1 组织权限**

1. 公司 / 用户 / 角色 / 权限数据模型与 Alembic 迁移  
2. 登录与 JWT  
3. 公司上下文（`X-Company-Id`）  
4. 前端登录页与按权限菜单  

---

## 附录 A — 术语

| 术语 | 说明 |
| --- | --- |
| 本位币 | 公司记账主币种，MVP 默认 CNY |
| 原币 | 单据交易币种 |
| 过账 | 单据生效并更新库存/财务余额的动作 |
| RBAC | 基于角色的访问控制 |

## 附录 B — 演示脚本（M5 目标）

1. 管理员登录  
2. 维护客户、供应商、物料、仓库  
3. 创建并确认采购订单 → 入库 → 查看库存  
4. 创建并确认销售订单 → 出库 → 查看库存与流水  
5. 查看应收应付与仪表盘
