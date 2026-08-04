# 数据库设计说明（全阶段）

| 项 | 说明 |
| --- | --- |
| 数据库 | MySQL 8.4（库名 `erp_demo`） |
| 字符集 | `utf8mb4` / `utf8mb4_unicode_ci` |
| ORM | SQLAlchemy 2.x |
| 迁移 | Alembic |
| 文档版本 | v0.3 |
| 更新日期 | 2026-08-05 |

---

## 1. 创建状态总览

> 状态以当前本机 `erp_demo` 库实际查询为准（2026-08-05）。

| 表名 | 阶段 | 用途 | 是否已创建 |
| --- | --- | --- | --- |
| `alembic_version` | M0 | Alembic 迁移版本记录 | **已创建** |
| `companies` | M1 | 公司/组织 | **已创建** |
| `users` | M1 | 用户 | **已创建** |
| `roles` | M1 | 角色 | **已创建** |
| `permissions` | M1 | 权限点 | **已创建** |
| `user_roles` | M1 | 用户-角色 | **已创建** |
| `role_permissions` | M1 | 角色-权限 | **已创建** |
| `user_companies` | M1 | 用户-公司（多公司预留） | **已创建** |
| `currencies` | M2 | 币种主数据 | **已创建** |
| `exchange_rates` | M2/P2 | 汇率（扩展） | 未创建 |
| `customers` | M2 | 客户 | **已创建** |
| `suppliers` | M2 | 供应商 | **已创建** |
| `materials` | M2 | 物料/产品 | **已创建** |
| `warehouses` | M2 | 仓库 | **已创建** |
| `inventory_balances` | M2 | 库存余额 | **已创建** |
| `inventory_transactions` | M2 | 出入库流水 | **已创建** |
| `document_sequences` | M3 | 单据编号序列 | **已创建** |
| `purchase_orders` | M3 | 采购订单头 | **已创建** |
| `purchase_order_lines` | M3 | 采购订单行 | **已创建** |
| `stock_in_orders` | M3 | 入库单头 | **已创建** |
| `stock_in_order_lines` | M3 | 入库单行 | **已创建** |
| `sales_orders` | M3 | 销售订单头 | **已创建** |
| `sales_order_lines` | M3 | 销售订单行 | **已创建** |
| `stock_out_orders` | M3 | 出库单头 | **已创建** |
| `stock_out_order_lines` | M3 | 出库单行 | **已创建** |
| `ap_bills` | M4 | 应付单 | **已创建** |
| `ar_bills` | M4 | 应收单 | **已创建** |
| `payment_records` | M4 | 付款登记 | **已创建** |
| `receipt_records` | M4 | 收款登记 | **已创建** |
| `audit_logs` | M5 | 操作审计（可选） | 未创建 |

**当前库内实际表：** 共 28 张（含 `alembic_version`），覆盖 M0–M4；未建表仅 `exchange_rates`、`audit_logs`。  
**Alembic 版本：** `20260805_0005`（`m4_finance`）。  
**活跃演示公司：** `USCO`（USD）、`EUCO`（EUR）；`DEFAULT` / `SECOND` 已停用。

---

## 2. 通用约定

### 2.1 审计字段（强制，适用于全部业务表）

> **硬性约定：** 除 Alembic 系统表 `alembic_version` 外，**所有业务表（含主表、明细表、关联/中间表）必须包含以下 4 个审计字段，不得省略。**

| 字段 | 类型 | 空值 | 说明 |
| --- | --- | --- | --- |
| `created_at` | DATETIME(6) NOT NULL | 否 | 创建时间；默认 `CURRENT_TIMESTAMP(6)` |
| `updated_at` | DATETIME(6) NOT NULL | 否 | 更新时间；修改时刷新 |
| `created_by` | BIGINT NULL | 可空 | 创建人，逻辑关联 `users.id`；系统种子可为 NULL |
| `updated_by` | BIGINT NULL | 可空 | 更新人，逻辑关联 `users.id` |

实现要求：

1. SQLAlchemy 使用统一 `AuditMixin`（或等价基类），新建模型默认带齐四字段。  
2. Alembic 迁移建表时必须写出四字段；Code Review 以此为检查项。  
3. 关联表（如 `user_roles`）同样保留四字段；建议另加代理主键 `id`，业务唯一约束用 UNIQUE。  
4. `users` 表自身的 `created_by`/`updated_by` 可指向其他用户或 NULL（自举场景）。  
5. 下文各表字段列表中，审计四字段一律完整列出，不再用「审计」二字省略。

### 2.2 其他公共字段（按表适用）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK AI | 主键（绝大多数表） |
| `company_id` | BIGINT NOT NULL | 公司隔离（组织主数据表自身除外；见各表） |
| `is_deleted` | TINYINT(1) DEFAULT 0 | 软删除（需要时使用） |

### 2.3 多币种字段（金额类单据）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `currency_code` | CHAR(3) | ISO 4217，如 CNY |
| `exchange_rate` | DECIMAL(18,8) | 相对本位币；MVP 固定 1 |
| `amount` | DECIMAL(18,2) | 原币金额 |
| `base_amount` | DECIMAL(18,2) | 本位币金额 |

### 2.4 命名与索引

- 表名、字段：`snake_case`
- 业务编码字段：`code`，同公司内唯一
- 状态字段：`status`（字符串枚举，见各表）
- 查询默认带 `company_id` 条件（适用表）

---

## 3. 表结构明细

### 3.1 M0 — 基础设施

#### `alembic_version`（已创建）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version_num` | VARCHAR(32) PK | 当前迁移版本 |

> 系统表，**不要求**审计字段。

---

### 3.2 M1 — 组织与权限

#### `companies`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `code` | VARCHAR(32) UNIQUE | 公司编码 |
| `name` | VARCHAR(128) | 公司名称 |
| `base_currency_code` | CHAR(3) | 本位币，默认 CNY |
| `status` | VARCHAR(16) | `active` / `inactive` |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `users`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `username` | VARCHAR(64) UNIQUE | 登录名 |
| `password_hash` | VARCHAR(255) | 密码哈希 |
| `display_name` | VARCHAR(64) | 显示名 |
| `email` | VARCHAR(128) NULL | 邮箱 |
| `status` | VARCHAR(16) | `active` / `disabled` |
| `last_login_at` | DATETIME(6) NULL | 最近登录 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `roles`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `code` | VARCHAR(64) UNIQUE | 如 `admin`、`sales` |
| `name` | VARCHAR(64) | 角色名 |
| `description` | VARCHAR(255) NULL | 说明 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `permissions`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `code` | VARCHAR(128) UNIQUE | 权限点，如 `sales.order.create` |
| `name` | VARCHAR(128) | 名称 |
| `module` | VARCHAR(64) | 模块分组 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `user_roles`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 代理主键 |
| `user_id` | BIGINT | FK → users |
| `role_id` | BIGINT | FK → roles |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`user_id`,`role_id`) | 业务唯一 |

#### `role_permissions`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 代理主键 |
| `role_id` | BIGINT | FK → roles |
| `permission_id` | BIGINT | FK → permissions |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`role_id`,`permission_id`) | 业务唯一 |

#### `user_companies`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 代理主键 |
| `user_id` | BIGINT | FK → users |
| `company_id` | BIGINT | FK → companies |
| `is_default` | TINYINT(1) | 是否默认公司 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`user_id`,`company_id`) | 业务唯一 |

---

### 3.3 M2 — 主数据与库存

#### `currencies`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | CHAR(3) PK | 币种代码 |
| `name` | VARCHAR(64) | 名称 |
| `symbol` | VARCHAR(8) NULL | 符号 |
| `decimal_places` | TINYINT | 小数位，默认 2 |
| `status` | VARCHAR(16) | `active` / `inactive` |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `exchange_rates`（P2 扩展，MVP 可不建）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `currency_code` | CHAR(3) | 外币 |
| `rate_date` | DATE | 汇率日期 |
| `rate` | DECIMAL(18,8) | 对本位币 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`currency_code`,`rate_date`) | |

#### `customers`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `code` | VARCHAR(32) | 客户编码 |
| `name` | VARCHAR(128) | 名称 |
| `contact_name` | VARCHAR(64) NULL | 联系人 |
| `contact_phone` | VARCHAR(32) NULL | 电话 |
| `credit_limit` | DECIMAL(18,2) NULL | 信用额度（简） |
| `status` | VARCHAR(16) | `active` / `inactive` |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`code`) | |

#### `suppliers`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `code` | VARCHAR(32) | 供应商编码 |
| `name` | VARCHAR(128) | 名称 |
| `contact_name` | VARCHAR(64) NULL | 联系人 |
| `contact_phone` | VARCHAR(32) NULL | 电话 |
| `status` | VARCHAR(16) | `active` / `inactive` |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`code`) | |

#### `materials`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `code` | VARCHAR(32) | 物料编码 |
| `name` | VARCHAR(128) | 名称 |
| `spec` | VARCHAR(128) NULL | 规格 |
| `uom` | VARCHAR(16) | 单位，如 pcs/kg |
| `material_type` | VARCHAR(32) | `finished` / `raw` / `other` |
| `status` | VARCHAR(16) | `active` / `inactive` |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`code`) | |

#### `warehouses`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `code` | VARCHAR(32) | 仓库编码 |
| `name` | VARCHAR(128) | 名称 |
| `is_default` | TINYINT(1) | 默认仓 |
| `status` | VARCHAR(16) | `active` / `inactive` |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`code`) | |

#### `inventory_balances`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `warehouse_id` | BIGINT | 仓库 |
| `material_id` | BIGINT | 物料 |
| `qty_on_hand` | DECIMAL(18,4) | 现存量 |
| `qty_available` | DECIMAL(18,4) | 可用量（MVP 可与现存量相同） |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`warehouse_id`,`material_id`) | |

#### `inventory_transactions`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `warehouse_id` | BIGINT | 仓库 |
| `material_id` | BIGINT | 物料 |
| `tx_type` | VARCHAR(32) | `in` / `out` / `adjust` |
| `direction` | TINYINT | `1` 入 / `-1` 出 |
| `qty` | DECIMAL(18,4) | 数量（正数） |
| `ref_doc_type` | VARCHAR(32) NULL | 来源单据类型 |
| `ref_doc_id` | BIGINT NULL | 来源单据 ID |
| `ref_doc_no` | VARCHAR(64) NULL | 来源单号 |
| `remark` | VARCHAR(255) NULL | 备注 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

---

### 3.4 M3 — 采销与出入库

#### `document_sequences`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `doc_type` | VARCHAR(32) | 如 `PO`/`SO`/`IN`/`OUT` |
| `prefix` | VARCHAR(16) | 前缀 |
| `next_value` | BIGINT | 下一序号 |
| `reset_rule` | VARCHAR(16) | `never` / `yearly` / `monthly` |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`doc_type`) | |

#### `purchase_orders`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `doc_no` | VARCHAR(64) | 单号 |
| `supplier_id` | BIGINT | 供应商 |
| `status` | VARCHAR(32) | `draft`/`confirmed`/`partial`/`completed`/`closed`/`cancelled` |
| `currency_code` | CHAR(3) | 币种 |
| `exchange_rate` | DECIMAL(18,8) | 汇率 |
| `tax_rate` | DECIMAL(8,4) NULL | 简税率 |
| `amount` | DECIMAL(18,2) | 原币合计 |
| `base_amount` | DECIMAL(18,2) | 本位币合计 |
| `order_date` | DATE | 订单日期 |
| `remark` | VARCHAR(255) NULL | 备注 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`doc_no`) | |

#### `purchase_order_lines`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `po_id` | BIGINT | 采购订单 |
| `line_no` | INT | 行号 |
| `material_id` | BIGINT | 物料 |
| `qty` | DECIMAL(18,4) | 订购数量 |
| `qty_received` | DECIMAL(18,4) | 已入库数量 |
| `unit_price` | DECIMAL(18,4) | 单价（原币） |
| `amount` | DECIMAL(18,2) | 行金额 |
| `base_amount` | DECIMAL(18,2) | 本位币 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `stock_in_orders`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `doc_no` | VARCHAR(64) | 入库单号 |
| `warehouse_id` | BIGINT | 仓库 |
| `po_id` | BIGINT | 关联采购订单 |
| `status` | VARCHAR(32) | `draft`/`posted`/`cancelled` |
| `posted_at` | DATETIME(6) NULL | 过账时间 |
| `remark` | VARCHAR(255) NULL | 备注 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`doc_no`) | |

#### `stock_in_order_lines`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `stock_in_id` | BIGINT | 入库单 |
| `line_no` | INT | 行号 |
| `po_line_id` | BIGINT NULL | 关联采购行 |
| `material_id` | BIGINT | 物料 |
| `qty` | DECIMAL(18,4) | 入库数量 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `sales_orders`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `doc_no` | VARCHAR(64) | 单号 |
| `customer_id` | BIGINT | 客户 |
| `status` | VARCHAR(32) | `draft`/`confirmed`/`partial`/`completed`/`closed`/`cancelled` |
| `currency_code` | CHAR(3) | 币种 |
| `exchange_rate` | DECIMAL(18,8) | 汇率 |
| `tax_rate` | DECIMAL(8,4) NULL | 简税率 |
| `amount` | DECIMAL(18,2) | 原币合计 |
| `base_amount` | DECIMAL(18,2) | 本位币合计 |
| `order_date` | DATE | 订单日期 |
| `remark` | VARCHAR(255) NULL | 备注 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`doc_no`) | |

#### `sales_order_lines`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `so_id` | BIGINT | 销售订单 |
| `line_no` | INT | 行号 |
| `material_id` | BIGINT | 物料 |
| `qty` | DECIMAL(18,4) | 订购数量 |
| `qty_shipped` | DECIMAL(18,4) | 已出库数量 |
| `unit_price` | DECIMAL(18,4) | 单价（原币） |
| `amount` | DECIMAL(18,2) | 行金额 |
| `base_amount` | DECIMAL(18,2) | 本位币 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `stock_out_orders`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `doc_no` | VARCHAR(64) | 出库单号 |
| `warehouse_id` | BIGINT | 仓库 |
| `so_id` | BIGINT | 关联销售订单 |
| `status` | VARCHAR(32) | `draft`/`posted`/`cancelled` |
| `posted_at` | DATETIME(6) NULL | 过账时间 |
| `remark` | VARCHAR(255) NULL | 备注 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`doc_no`) | |

#### `stock_out_order_lines`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `stock_out_id` | BIGINT | 出库单 |
| `line_no` | INT | 行号 |
| `so_line_id` | BIGINT NULL | 关联销售行 |
| `material_id` | BIGINT | 物料 |
| `qty` | DECIMAL(18,4) | 出库数量 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

---

### 3.5 M4 — 财务简版

#### `ap_bills`（应付）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `doc_no` | VARCHAR(64) | 应付单号 |
| `supplier_id` | BIGINT | 供应商 |
| `source_type` | VARCHAR(32) | 来源类型（如 `stock_in`） |
| `source_id` | BIGINT | 来源单据 ID |
| `currency_code` | CHAR(3) | 币种 |
| `exchange_rate` | DECIMAL(18,8) | 汇率 |
| `amount` | DECIMAL(18,2) | 原币应付 |
| `base_amount` | DECIMAL(18,2) | 本位币应付 |
| `paid_amount` | DECIMAL(18,2) | 已付原币 |
| `status` | VARCHAR(32) | `open`/`partial`/`paid`/`void` |
| `bill_date` | DATE | 账单日 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`doc_no`) | |

#### `ar_bills`（应收）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `doc_no` | VARCHAR(64) | 应收单号 |
| `customer_id` | BIGINT | 客户 |
| `source_type` | VARCHAR(32) | 来源类型（如 `stock_out`） |
| `source_id` | BIGINT | 来源单据 ID |
| `currency_code` | CHAR(3) | 币种 |
| `exchange_rate` | DECIMAL(18,8) | 汇率 |
| `amount` | DECIMAL(18,2) | 原币应收 |
| `base_amount` | DECIMAL(18,2) | 本位币应收 |
| `received_amount` | DECIMAL(18,2) | 已收原币 |
| `status` | VARCHAR(32) | `open`/`partial`/`paid`/`void` |
| `bill_date` | DATE | 账单日 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |
| UNIQUE | (`company_id`,`doc_no`) | |

#### `payment_records`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `ap_bill_id` | BIGINT | 应付单 |
| `amount` | DECIMAL(18,2) | 本次付款原币 |
| `base_amount` | DECIMAL(18,2) | 本位币 |
| `currency_code` | CHAR(3) | 币种 |
| `exchange_rate` | DECIMAL(18,8) | 汇率 |
| `pay_date` | DATE | 付款日 |
| `status` | VARCHAR(32) | `posted`/`void` |
| `remark` | VARCHAR(255) NULL | 备注 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

#### `receipt_records`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT | 公司 |
| `ar_bill_id` | BIGINT | 应收单 |
| `amount` | DECIMAL(18,2) | 本次收款原币 |
| `base_amount` | DECIMAL(18,2) | 本位币 |
| `currency_code` | CHAR(3) | 币种 |
| `exchange_rate` | DECIMAL(18,8) | 汇率 |
| `pay_date` | DATE | 收款日 |
| `status` | VARCHAR(32) | `posted`/`void` |
| `remark` | VARCHAR(255) NULL | 备注 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

---

### 3.6 M5 — 可选增强

#### `audit_logs`（可选）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | BIGINT PK | 主键 |
| `company_id` | BIGINT NULL | 公司（全局操作可空） |
| `user_id` | BIGINT NULL | 操作人（业务含义；可与 created_by 同值） |
| `action` | VARCHAR(64) | 动作 |
| `entity_type` | VARCHAR(64) | 实体类型 |
| `entity_id` | BIGINT NULL | 实体 ID |
| `detail_json` | JSON NULL | 详情 |
| `created_at` | DATETIME(6) NOT NULL | 创建时间 |
| `updated_at` | DATETIME(6) NOT NULL | 更新时间 |
| `created_by` | BIGINT NULL | 创建人 |
| `updated_by` | BIGINT NULL | 更新人 |

M5 以种子数据与演示打磨为主，可不强制新建业务表。

---

## 4. 阶段与建表映射

| 阶段 | 新建表 |
| --- | --- |
| M0 | `alembic_version`（Alembic 自动） |
| M1 | companies, users, roles, permissions, user_roles, role_permissions, user_companies |
| M2 | currencies, customers, suppliers, materials, warehouses, inventory_balances, inventory_transactions；（可选）exchange_rates |
| M3 | document_sequences, purchase_orders, purchase_order_lines, stock_in_*, sales_orders, sales_order_lines, stock_out_* |
| M4 | ap_bills, ar_bills, payment_records, receipt_records |
| M5 | （可选）audit_logs |

---

## 5. 迁移版本规划（建议）

| Revision | 阶段 | 内容 |
| --- | --- | --- |
| `20260804_0001` | M0 | 空基线（**不是备份**；仅占迁移链起点，**已应用**） |
| `20260805_0002` | M1 | 组织权限表（**已应用**） |
| `m2_master_inventory` | M2 | 主数据 + 库存 |
| `m3_purchase_sales` | M3 | 采销出入库 |
| `m4_finance` | M4 | 应收应付收付款 |
| `m5_audit_optional` | M5 | 可选审计表 |

---

## 6. 如何核对「是否已创建」

```bash
mysql -uroot -p -e "USE erp_demo; SHOW TABLES;"
```

或：

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'erp_demo'
ORDER BY table_name;
```

核对某表是否具备审计四字段：

```sql
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'erp_demo'
  AND table_name = 'your_table'
  AND column_name IN ('created_at','updated_at','created_by','updated_by');
```

更新本文件时，请同步修改第 1 节「是否已创建」列。
