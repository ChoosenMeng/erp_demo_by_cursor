# M4 阶段说明 — 财务简版 + 仪表盘

| 项 | 内容 |
| --- | --- |
| 阶段 | M4 |
| 状态 | **已完成** |
| 目标 | 应收应付可查询；收付款可登记；仪表盘展示真实汇总 |
| 前置 | M3 完成 |
| 关联文档 | [database.md](./database.md) |

---

## 1. 功能需求

| ID | 需求 | 优先级 |
| --- | --- | --- |
| M4-F01 | 采购确认或入库过账后生成应付（规则固定并文档化） | P1 |
| M4-F02 | 销售确认或出库过账后生成应收 | P1 |
| M4-F03 | 应付/应收列表与详情查询 | P1 |
| M4-F04 | 付款/收款登记，更新已付/已收与单据状态 | P1 |
| M4-F05 | 金额含原币/本位币（MVP 汇率=1） | P1 |
| M4-F06 | 仪表盘：今日/本月销售额、采购额、库存 SKU 数、待办订单数 | P1 |
| M4-F07 | 近 7/30 日销售趋势 | P1 |
| M4-F08 | 完整会计凭证/总账 | 不做 |

### 建议生成规则（可在实现时二选一并写死）

| 单据 | 触发点（推荐） |
| --- | --- |
| 应付 `ap_bills` | 采购入库单过账成功 |
| 应收 `ar_bills` | 销售出库单过账成功 |

---

## 2. 用例

### UC-M4-01 入库生成应付

1. 完成采购入库过账  
2. 自动生成应付单，金额与入库/PO 一致  
3. 财务列表可见 `status=open`  

### UC-M4-02 付款核销

1. 对应付登记一笔付款  
2. `paid_amount` 增加；足额后 `status=paid`  

### UC-M4-03 出库生成应收并收款

对称应付流程。

### UC-M4-04 查看仪表盘

1. 打开仪表盘  
2. 指标来自真实订单/库存/财务数据，非写死常量  

---

## 3. 需要用到的数据库表

| 表 | 说明 | 本阶段创建 |
| --- | --- | --- |
| `ap_bills` | 应付 | 是 |
| `ar_bills` | 应收 | 是 |
| `payment_records` | 付款记录 | 是 |
| `receipt_records` | 收款记录 | 是 |
| M3 采销出入库表 | 触发来源 | 依赖 |
| M2 库存/主数据 | 仪表盘统计 | 依赖 |

字段详见 [database.md §3.5](./database.md)。

---

## 4. 需要编写的接口

前缀：`/api/v1/finance`、`/api/v1/dashboard`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/finance/ap-bills` | 应付列表 |
| GET | `/finance/ap-bills/{id}` | 应付详情 |
| POST | `/finance/ap-bills/{id}/payments` | 登记付款 |
| GET | `/finance/ar-bills` | 应收列表 |
| GET | `/finance/ar-bills/{id}` | 应收详情 |
| POST | `/finance/ar-bills/{id}/receipts` | 登记收款 |
| GET | `/dashboard/summary` | 关键指标 |
| GET | `/dashboard/sales-trend?days=7` | 销售趋势 |

> 应付/应收的「创建」主要由 M3 过账流程内部调用服务完成，可不开放手工创建 API（或仅管理员调试用）。

---

## 5. 简要接口文档

### 5.1 `GET /api/v1/finance/ap-bills?status=open`

**响应 data.items[]**

```json
{
  "id": 1,
  "doc_no": "AP202608050001",
  "supplier_id": 1,
  "supplier_name": "供应商A",
  "amount": "1250.00",
  "base_amount": "1250.00",
  "paid_amount": "0.00",
  "currency_code": "CNY",
  "status": "open",
  "bill_date": "2026-08-05",
  "source_type": "stock_in",
  "source_id": 9
}
```

### 5.2 `POST /api/v1/finance/ap-bills/{id}/payments`

**请求**

```json
{ "amount": "500.00", "pay_date": "2026-08-06", "remark": "首付款" }
```

**响应 data：** 付款记录 + 更新后的应付单状态。

### 5.3 `GET /api/v1/dashboard/summary`

```json
{
  "sales_amount_today": "0.00",
  "sales_amount_month": "12800.00",
  "purchase_amount_month": "5600.00",
  "inventory_sku_count": 12,
  "pending_so_count": 3,
  "pending_po_count": 1
}
```

### 5.4 `GET /api/v1/dashboard/sales-trend?days=7`

```json
{
  "points": [
    { "date": "2026-08-01", "amount": "1200.00" },
    { "date": "2026-08-02", "amount": "800.00" }
  ]
}
```

---

## 6. 前端页面

- 应付列表/详情 + 付款  
- 应收列表/详情 + 收款  
- 仪表盘（指标卡片 + 简单折线/柱状图）  

---

## 7. 验收标准

- 出入库后自动产生应收/应付  
- 收付款后状态正确  
- 仪表盘数值与业务数据一致  
- 单测覆盖「生成规则」与「超额付款拒绝」  

---

## 8. 下一阶段

完成后进入 **[M5](./m5_status.md)**：打磨、种子数据、演示脚本。
