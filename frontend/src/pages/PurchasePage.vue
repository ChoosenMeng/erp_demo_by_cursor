<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost } from '../api/client'
import { useAuthStore } from '../stores/auth'

type Line = {
  id: number
  material_id: number
  qty: string
  qty_received: string
  unit_price: string
}

type PO = {
  id: number
  doc_no: string
  supplier_id: number
  status: string
  amount: string
  base_amount: string
  currency_code: string
  exchange_rate: string
  order_date: string
  lines: Line[]
}

type Currency = { code: string; name: string }

type StockIn = {
  id: number
  doc_no: string
  po_id: number
  warehouse_id: number
  status: string
}

type Option = { id: number; code: string; name: string }

const auth = useAuthStore()
const orders = ref<PO[]>([])
const stockIns = ref<StockIn[]>([])
const suppliers = ref<Option[]>([])
const materials = ref<Option[]>([])
const warehouses = ref<Option[]>([])
const currencies = ref<Currency[]>([])
const error = ref('')
const form = ref({
  supplier_id: 0,
  order_date: new Date().toISOString().slice(0, 10),
  material_id: 0,
  qty: '10',
  unit_price: '12.5',
  currency_code: 'CNY',
  exchange_rate: '1',
})
const inForm = ref({
  po_id: 0,
  warehouse_id: 0,
})

async function load() {
  error.value = ''
  try {
    const [po, si, s, m, w, c] = await Promise.all([
      apiGet<{ items: PO[] }>('/api/v1/purchase/orders'),
      apiGet<{ items: StockIn[] }>('/api/v1/purchase/stock-ins'),
      apiGet<{ items: Option[] }>('/api/v1/master/suppliers'),
      apiGet<{ items: Option[] }>('/api/v1/master/materials'),
      apiGet<{ items: Option[] }>('/api/v1/master/warehouses'),
      apiGet<Currency[]>('/api/v1/master/currencies'),
    ])
    orders.value = po.data.items
    stockIns.value = si.data.items
    suppliers.value = s.data.items
    materials.value = m.data.items
    warehouses.value = w.data.items
    currencies.value = c.data
    const base = auth.activeCompany.value?.base_currency_code ?? 'CNY'
    form.value.currency_code = base
    form.value.exchange_rate = '1'
    if (!form.value.supplier_id && suppliers.value[0]) form.value.supplier_id = suppliers.value[0].id
    if (!form.value.material_id && materials.value[0]) form.value.material_id = materials.value[0].id
    if (!inForm.value.warehouse_id && warehouses.value[0]) {
      inForm.value.warehouse_id = warehouses.value[0].id
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

async function createPo() {
  error.value = ''
  try {
    await apiPost('/api/v1/purchase/orders', {
      supplier_id: Number(form.value.supplier_id),
      order_date: form.value.order_date,
      currency_code: form.value.currency_code,
      exchange_rate: form.value.exchange_rate,
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

async function confirmPo(id: number) {
  error.value = ''
  try {
    await apiPost(`/api/v1/purchase/orders/${id}/confirm`)
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '确认失败'
  }
}

async function createAndPostIn(po: PO) {
  error.value = ''
  try {
    const line = po.lines[0]
    if (!line) throw new Error('订单无明细')
    const created = await apiPost<StockIn>('/api/v1/purchase/stock-ins', {
      warehouse_id: Number(inForm.value.warehouse_id),
      po_id: po.id,
      lines: [
        {
          po_line_id: line.id,
          material_id: line.material_id,
          qty: line.qty,
        },
      ],
    })
    await apiPost(`/api/v1/purchase/stock-ins/${created.data.id}/post`)
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '入库失败'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <h1>采购</h1>
    <p>
      流程：创建草稿 → 确认 → 入库过账。当前公司本位币：
      {{ auth.activeCompany.value?.base_currency_code ?? '-' }}。可开外币单并填汇率（换算本位币）。
    </p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h2>新建采购订单</h2>
      <div class="form-grid">
        <select v-model.number="form.supplier_id">
          <option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.code }} {{ s.name }}</option>
        </select>
        <input v-model="form.order_date" type="date" />
        <select v-model.number="form.material_id">
          <option v-for="m in materials" :key="m.id" :value="m.id">{{ m.code }} {{ m.name }}</option>
        </select>
        <input v-model="form.qty" placeholder="数量" />
        <input v-model="form.unit_price" placeholder="单价（原币）" />
        <select v-model="form.currency_code">
          <option v-for="c in currencies" :key="c.code" :value="c.code">
            {{ c.code }} {{ c.name }}
          </option>
        </select>
        <input v-model="form.exchange_rate" placeholder="汇率→本位币" />
        <button type="button" @click="createPo">创建草稿</button>
      </div>
    </div>

    <div class="card">
      <h2>入库仓库</h2>
      <select v-model.number="inForm.warehouse_id">
        <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.code }} {{ w.name }}</option>
      </select>
    </div>

    <div class="card">
      <h2>采购订单</h2>
      <table>
        <thead>
          <tr>
            <th>单号</th>
            <th>状态</th>
            <th>原币</th>
            <th>本位币</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="po in orders" :key="po.id">
            <td>{{ po.doc_no }}</td>
            <td>{{ po.status }}</td>
            <td>{{ po.amount }} {{ po.currency_code }} @{{ po.exchange_rate }}</td>
            <td>{{ po.base_amount }}</td>
            <td class="ops">
              <button v-if="po.status === 'draft'" type="button" @click="confirmPo(po.id)">确认</button>
              <button
                v-if="po.status === 'confirmed' || po.status === 'partial'"
                type="button"
                @click="createAndPostIn(po)"
              >
                入库过账
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>入库单</h2>
      <table>
        <thead>
          <tr>
            <th>单号</th>
            <th>PO</th>
            <th>仓库</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in stockIns" :key="row.id">
            <td>{{ row.doc_no }}</td>
            <td>{{ row.po_id }}</td>
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
