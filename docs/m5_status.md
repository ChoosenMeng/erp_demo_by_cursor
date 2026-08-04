# M5 阶段说明 — 打磨与演示

| 项 | 内容 |
| --- | --- |
| 阶段 | M5 |
| 状态 | **已完成** |
| 目标 | 可演示、可交接；文档与种子数据齐全；缺陷收敛 |
| 前置 | M4 完成 |
| 关联文档 | [database.md](./database.md)、[README.md](../README.md)、[backlog.md](./backlog.md) |

---

## 1. 功能需求（完成情况）

| ID | 需求 | 优先级 | 状态 |
| --- | --- | --- | --- |
| M5-F01 | 演示种子数据脚本 | P0 | 已完成（`python -m app.scripts.seed`） |
| M5-F02 | 可选第二公司种子 | P1 | 已完成（`--with-second-company`） |
| M5-F03 | 模块说明 / OpenAPI 分组 | P0 | 已完成（路由 tags + `/docs`） |
| M5-F04 | 关键 API 集成测试 | P1 | 已完成（trade/finance/demo_seed） |
| M5-F05 | 演示脚本文档 | P0 | 已完成（见下节 / README 附录 B） |
| M5-F06 | 已知问题与 Backlog | P0 | 已完成（[backlog.md](./backlog.md)） |
| M5-F07 | Docker Compose | P2 | 未做（列入 backlog） |
| M5-F08 | 操作审计表 | P2 | 未做（列入 backlog） |

---

## 2. 种子命令

```bash
conda activate cursor-erp-demo
cd backend
alembic upgrade head
python -m app.scripts.seed
# 可选：第二公司隔离冒烟
python -m app.scripts.seed --with-second-company
```

默认账号：`admin` / `admin123`  
默认公司主数据：`CUS001` / `SUP001` / `FG-001` / `RM-001` / `WH-MAIN`。

---

## 3. 15 分钟演示脚本

1. 启动后端（`:8000`）与前端（`:5173`）  
2. 使用 `admin` / `admin123` 登录  
3. 打开客户 / 供应商 / 物料 / 仓库，确认种子主数据存在  
4. **采购**：新建订单（选 SUP001 + FG-001）→ 确认 → 入库过账 → 库存页看余额  
5. **销售**：新建订单（选 CUS001 + FG-001）→ 确认 → 出库过账 → 库存/流水可追溯  
6. **财务**：查看应付/应收，登记一笔付款或收款  
7. **仪表盘**：确认本月销售额/采购额与待办订单非写死常量  

---

## 4. 验收标准

| 标准 | 结果 |
| --- | --- |
| 冷启动 | README + 本文件可完成启动与种子 |
| 主路径 | 采销库存财务仪表盘可演示 |
| 质量 | pytest 覆盖主路径；已知问题见 backlog |
| 扩展验证 | `--with-second-company` + 隔离测试通过 |

---

## 5. 全阶段索引

| 文档 | 阶段 |
| --- | --- |
| [m0_status.md](./m0_status.md) | 脚手架 |
| [m1_status.md](./m1_status.md) | 组织权限 |
| [m2_status.md](./m2_status.md) | 主数据库存 |
| [m3_status.md](./m3_status.md) | 采销闭环 |
| [m4_status.md](./m4_status.md) | 财务仪表盘 |
| [m5_status.md](./m5_status.md) | 打磨演示（本文） |
| [database.md](./database.md) | 全库表字段与创建状态 |
| [backlog.md](./backlog.md) | 已知问题与下一期 |
