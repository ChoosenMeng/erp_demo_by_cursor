# M2 阶段说明 — 主数据 + 库存核心

| 项 | 内容 |
| --- | --- |
| 阶段 | M2 |
| 状态 | **已完成** |
| 目标 | 客户/供应商/物料/仓库可维护；库存余额与流水服务可用 |
| 前置 | M1 完成（鉴权 + 公司上下文） |
| 关联文档 | [database.md](./database.md) |

---

## 1. 功能需求

| ID | 需求 | 优先级 |
| --- | --- | --- |
| M2-F01 | 客户 CRUD（公司内编码唯一） | P0 |
| M2-F02 | 供应商 CRUD | P0 |
| M2-F03 | 物料/产品 CRUD（类型：成品/原材料等） | P0 |
| M2-F04 | 仓库 CRUD；支持默认仓 | P0 |
| M2-F05 | 币种主数据（至少 CNY）；公司本位币只读展示 | P1（模型 P0） |
| M2-F06 | 库存余额查询（公司+仓+物料） | P0 |
| M2-F07 | 出入库流水查询 | P0 |
| M2-F08 | 库存服务：入库增加、出库扣减、不足则拒绝并回滚 | P0 |
| M2-F09 | 汇率表维护 | P2 |
| M2-F10 | 盘点/调拨 | P2 |

> 说明：M2 可提供「调试用」库存调整接口，或仅服务层供 M3 出入库单据调用；推荐服务层优先，UI 以查询为主。

---

## 2. 用例

### UC-M2-01 维护主数据

1. 登录后进入客户/供应商/物料/仓库页面  
2. 创建并编辑记录  
3. 同公司重复编码被拒绝  

### UC-M2-02 查询库存

1. 选择仓库查看物料余额  
2. 无流水时余额为 0 或不存在记录  

### UC-M2-03 库存扣减不足回滚

1. 服务层对某物料出库数量大于可用量  
2. 事务回滚，余额不变，返回业务错误  

### UC-M2-04 入库后余额正确

1. 调用库存入库服务（或调试接口）  
2. `inventory_balances` 增加，`inventory_transactions` 新增一条  

---

## 3. 需要用到的数据库表

| 表 | 说明 | 本阶段创建 |
| --- | --- | --- |
| `currencies` | 币种 | 是 |
| `customers` | 客户 | 是 |
| `suppliers` | 供应商 | 是 |
| `materials` | 物料 | 是 |
| `warehouses` | 仓库 | 是 |
| `inventory_balances` | 库存余额 | 是 |
| `inventory_transactions` | 出入库流水 | 是 |
| `exchange_rates` | 汇率 | 可选（P2） |
| M1 组织表 | 公司上下文/鉴权 | 已存在（依赖） |

字段详见 [database.md §3.3](./database.md)。

---

## 4. 需要编写的接口

前缀：`/api/v1/master` 与 `/api/v1/inventory`  
均需登录 + 公司上下文。

### 4.1 主数据

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET/POST | `/master/customers` | 列表/创建 |
| GET/PATCH/DELETE | `/master/customers/{id}` | 详情/更新/停用或软删 |
| GET/POST | `/master/suppliers` | 供应商 |
| GET/PATCH/DELETE | `/master/suppliers/{id}` | |
| GET/POST | `/master/materials` | 物料 |
| GET/PATCH/DELETE | `/master/materials/{id}` | |
| GET/POST | `/master/warehouses` | 仓库 |
| GET/PATCH | `/master/warehouses/{id}` | |
| GET | `/master/currencies` | 币种列表 |
| POST | `/master/currencies` | 新增币种（管理员） |

### 4.2 库存

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/inventory/balances` | 余额列表，支持 warehouse_id/material_id |
| GET | `/inventory/transactions` | 流水分页 |
| POST | `/inventory/adjust` | （可选）调试调整入库/出库 |

**领域服务（非必须暴露 HTTP）：**

- `InventoryService.increase(...)`  
- `InventoryService.decrease(...)` — 不足抛 `AppError`  

---

## 5. 简要接口文档

### 5.1 `POST /api/v1/master/materials`

**请求**

```json
{
  "code": "RM-001",
  "name": "铝合金板",
  "spec": "2mm",
  "uom": "kg",
  "material_type": "raw",
  "status": "active"
}
```

**响应 data：** 完整物料对象（含 `id`、`company_id`）。

### 5.2 `GET /api/v1/inventory/balances?warehouse_id=1`

**响应 data**

```json
{
  "items": [
    {
      "warehouse_id": 1,
      "warehouse_name": "成品仓",
      "material_id": 10,
      "material_code": "FG-001",
      "material_name": "成品A",
      "qty_on_hand": "100.0000",
      "qty_available": "100.0000"
    }
  ],
  "meta": { "page": 1, "page_size": 20, "total": 1 }
}
```

### 5.3 `POST /api/v1/inventory/adjust`（可选）

**请求**

```json
{
  "warehouse_id": 1,
  "material_id": 10,
  "direction": 1,
  "qty": "20",
  "remark": "期初入库"
}
```

**错误：** 出库不足时 `code=400xx`，message 如「库存不足」。

---

## 6. 前端页面

- 客户 / 供应商 / 物料 / 仓库列表与表单  
- 库存余额查询  
- 库存流水查询  

---

## 7. 验收标准

- 主数据可维护，公司内编码唯一  
- 入库后余额与流水正确  
- 出库不足事务回滚（pytest 覆盖）  
- 所有查询强制公司作用域  

---

## 8. 下一阶段

完成后进入 **[M3](./m3_status.md)**：采购/销售订单与出入库过账闭环。
