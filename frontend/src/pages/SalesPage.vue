<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost } from '../api/client'

type Line = {
  id: number
  material_id: number
  qty: string
  qty_shipped: string
  unit_price: string
}

type SO = {
  id: number
  doc_no: string
  customer_id: number
  status: string
  amount: string
  lines: Line[]
}

type StockOut = {
  id: number
  doc_no: string
  so_id: number
  warehouse_id: number
  status: string
}

type Option = { id: number; code: string; name: string }

const orders = ref<SO[]>([])
const stockOuts = ref<StockOut[]>([])
const customers = ref<Option[]>([])
const materials = ref<Option[]>([])
const warehouses = ref<Option[]>([])
const error = ref('')
const form = ref({
  customer_id: 0,
  order_date: new Date().toISOString().slice(0, 10),
  material_id: 0,
  qty: '5',
  unit_price: '20',
})
const outForm = ref({ warehouse_id: 0 })

async function load() {
  error.value = ''
  try {
    const [so, outs, c, m, w] = await Promise.all([
      apiGet<{ items: SO[] }>('/api/v1/sales/orders'),
      apiGet<{ items: StockOut[] }>('/api/v1/sales/stock-outs'),
      apiGet<{ items: Option[] }>('/api/v1/master/customers'),
      apiGet<{ items: Option[] }>('/api/v1/master/materials'),
      apiGet<{ items: Option[] }>('/api/v1/master/warehouses'),
    ])
    orders.value = so.data.items
    stockOuts.value = outs.data.items
    customers.value = c.data.items
    materials.value = m.data.items
    warehouses.value = w.data.items
    if (!form.value.customer_id && customers.value[0]) form.value.customer_id = customers.value[0].id
    if (!form.value.material_id && materials.value[0]) form.value.material_id = materials.value[0].id
    if (!outForm.value.warehouse_id && warehouses.value[0]) {
      outForm.value.warehouse_id = warehouses.value[0].id
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

async function createSo() {
  error.value = ''
  try {
    await apiPost('/api/v1/sales/orders', {
      customer_id: Number(form.value.customer_id),
      order_date: form.value.order_date,
      currency_code: 'CNY',
      lines: [
        {
          material_id: Number(form.value.material_id),
          qty: form.value.qty,
          unit_price: form.value.unit_price,
        },
      ],
    })
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '创建失败'
  }
}

async function confirmSo(id: number) {
  error.value = ''
  try {
    await apiPost(`/api/v1/sales/orders/${id}/confirm`)
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '确认失败'
  }
}

async function createAndPostOut(so: SO) {
  error.value = ''
  try {
    const line = so.lines[0]
    if (!line) throw new Error('订单无明细')
    const created = await apiPost<StockOut>('/api/v1/sales/stock-outs', {
      warehouse_id: Number(outForm.value.warehouse_id),
      so_id: so.id,
      lines: [
        {
          so_line_id: line.id,
          material_id: line.material_id,
          qty: line.qty,
        },
      ],
    })
    await apiPost(`/api/v1/sales/stock-outs/${created.data.id}/post`)
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '出库失败'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <h1>销售</h1>
    <p>流程：创建草稿 → 确认 → 出库过账（库存不足会失败）。权限：`sales.read` / `sales.write`。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h2>新建销售订单</h2>
      <div class="form-grid">
        <select v-model.number="form.customer_id">
          <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.code }} {{ c.name }}</option>
        </select>
        <input v-model="form.order_date" type="date" />
        <select v-model.number="form.material_id">
          <option v-for="m in materials" :key="m.id" :value="m.id">{{ m.code }} {{ m.name }}</option>
        </select>
        <input v-model="form.qty" placeholder="数量" />
        <input v-model="form.unit_price" placeholder="单价" />
        <button type="button" @click="createSo">创建草稿</button>
      </div>
    </div>

    <div class="card">
      <h2>出库仓库</h2>
      <select v-model.number="outForm.warehouse_id">
        <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.code }} {{ w.name }}</option>
      </select>
    </div>

    <div class="card">
      <h2>销售订单</h2>
      <table>
        <thead>
          <tr>
            <th>单号</th>
            <th>状态</th>
            <th>金额</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="so in orders" :key="so.id">
            <td>{{ so.doc_no }}</td>
            <td>{{ so.status }}</td>
            <td>{{ so.amount }}</td>
            <td class="ops">
              <button v-if="so.status === 'draft'" type="button" @click="confirmSo(so.id)">确认</button>
              <button
                v-if="so.status === 'confirmed' || so.status === 'partial'"
                type="button"
                @click="createAndPostOut(so)"
              >
                出库过账
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>出库单</h2>
      <table>
        <thead>
          <tr>
            <th>单号</th>
            <th>SO</th>
            <th>仓库</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in stockOuts" :key="row.id">
            <td>{{ row.doc_no }}</td>
            <td>{{ row.so_id }}</td>
            <td>{{ row.warehouse_id }}</td>
            <td>{{ row.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.page h1 {
  margin: 0 0 0.35rem;
}
.page p {
  color: #4b5c5b;
}
.error {
  color: #b91c1c;
}
.card {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(28, 43, 42, 0.08);
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.5rem;
}
input,
select,
button {
  padding: 0.55rem 0.65rem;
  border-radius: 0.45rem;
  border: 1px solid rgba(28, 43, 42, 0.16);
  font: inherit;
}
button {
  background: #0f766e;
  color: #fff;
  border: 0;
  cursor: pointer;
  font-weight: 600;
}
.ops {
  display: flex;
  gap: 0.4rem;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  text-align: left;
  padding: 0.55rem 0.35rem;
  border-bottom: 1px solid rgba(28, 43, 42, 0.08);
}
</style>
