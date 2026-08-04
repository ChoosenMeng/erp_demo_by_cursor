# M3 阶段说明 — 采销闭环

| 项 | 内容 |
| --- | --- |
| 阶段 | M3 |
| 状态 | **未开始** |
| 目标 | 采购入库 → 销售出库全流程可走通；库存与订单状态一致 |
| 前置 | M2 完成 |
| 关联文档 | [database.md](./database.md) |

---

## 1. 功能需求

| ID | 需求 | 优先级 |
| --- | --- | --- |
| M3-F01 | 采购订单 CRUD + 状态机 | P0 |
| M3-F02 | 采购入库单：关联 PO，过账增加库存 | P0 |
| M3-F03 | 销售订单 CRUD + 状态机 | P0 |
| M3-F04 | 销售出库单：关联 SO，过账扣减库存 | P0 |
| M3-F05 | 单据编号规则（按公司可配置，`document_sequences`） | P0 |
| M3-F06 | 前端：订单列表/详情、确认、入出库操作 | P0 |
| M3-F07 | 订单金额字段含币种/汇率/本位币（MVP 汇率=1） | P0 |
| M3-F08 | 询价单 / 报价单 | P2 |

### 订单状态机

```text
draft → confirmed → partial / completed → closed
         ↘ cancelled（未发生入出库时可取消）
```

---

## 2. 用例

### UC-M3-01 采购入库

1. 创建采购订单（草稿）并添加明细  
2. 确认订单  
3. 创建入库单并过账  
4. 库存增加；PO 行 `qty_received` 更新；状态变为 partial/completed  

### UC-M3-02 销售出库

1. 创建并确认销售订单  
2. 创建出库单；库存不足则过账失败  
3. 成功后库存减少；SO 状态更新  

### UC-M3-03 单据编号

1. 同公司连续创建 PO，单号按序列递增且不重复  

### UC-M3-04 端到端演示

1. 采购入库后再销售出库  
2. 库存与流水可追溯到来源单号  

---

## 3. 需要用到的数据库表

| 表 | 说明 | 本阶段创建 |
| --- | --- | --- |
| `document_sequences` | 单号序列 | 是 |
| `purchase_orders` | 采购订单头 | 是 |
| `purchase_order_lines` | 采购订单行 | 是 |
| `stock_in_orders` | 入库单头 | 是 |
| `stock_in_order_lines` | 入库单行 | 是 |
| `sales_orders` | 销售订单头 | 是 |
| `sales_order_lines` | 销售订单行 | 是 |
| `stock_out_orders` | 出库单头 | 是 |
| `stock_out_order_lines` | 出库单行 | 是 |
| M2 主数据/库存表 | 关联与过账 | 依赖 |
| M1 组织表 | 鉴权与公司 | 依赖 |

字段详见 [database.md §3.4](./database.md)。

---

## 4. 需要编写的接口

### 4.1 采购 `/api/v1/purchase`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET/POST | `/purchase/orders` | 列表/创建 |
| GET/PATCH | `/purchase/orders/{id}` | 详情/改草稿 |
| POST | `/purchase/orders/{id}/confirm` | 确认 |
| POST | `/purchase/orders/{id}/cancel` | 取消 |
| GET/POST | `/purchase/stock-ins` | 入库单列表/创建 |
| POST | `/purchase/stock-ins/{id}/post` | 过账入库 |

### 4.2 销售 `/api/v1/sales`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET/POST | `/sales/orders` | 列表/创建 |
| GET/PATCH | `/sales/orders/{id}` | 详情/改草稿 |
| POST | `/sales/orders/{id}/confirm` | 确认 |
| POST | `/sales/orders/{id}/cancel` | 取消 |
| GET/POST | `/sales/stock-outs` | 出库单列表/创建 |
| POST | `/sales/stock-outs/{id}/post` | 过账出库 |

---

## 5. 简要接口文档

### 5.1 `POST /api/v1/purchase/orders`

**请求**

```json
{
  "supplier_id": 1,
  "order_date": "2026-08-05",
  "currency_code": "CNY",
  "tax_rate": 0.13,
  "remark": "",
  "lines": [
    { "material_id": 10, "qty": "100", "unit_price": "12.5" }
  ]
}
```

**响应 data：** 订单头 + lines；`status=draft`；已生成 `doc_no`。

### 5.2 `POST /api/v1/purchase/stock-ins/{id}/post`

**行为（事务内）：**

1. 校验入库单与 PO 状态  
2. 调用 `InventoryService.increase`  
3. 写 `inventory_transactions`  
4. 更新 PO 行已收数量与订单状态  
5. 入库单 `status=posted`  

**失败：** 参数非法 / 状态不允许 → 4xx，数据不变。

### 5.3 `POST /api/v1/sales/stock-outs/{id}/post`

对称入库；调用 `decrease`；库存不足返回业务错误且不改单。

---

## 6. 前端页面

- 采购订单列表/详情（含确认、取消）  
- 入库单创建与过账  
- 销售订单列表/详情  
- 出库单创建与过账  

---

## 7. 验收标准

- UI 可走通：采购确认→入库→销售确认→出库  
- 库存数量、流水、订单状态一致  
- 超卖被拒绝  
- 单号公司内唯一  

---

## 8. 下一阶段

完成后进入 **[M4](./m4_status.md)**：简版财务 + 仪表盘。
