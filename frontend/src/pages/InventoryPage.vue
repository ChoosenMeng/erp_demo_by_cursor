<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost } from '../api/client'

type Balance = {
  warehouse_id: number
  warehouse_name: string
  material_id: number
  material_code: string
  material_name: string
  qty_on_hand: string
  qty_available: string
}

type Tx = {
  id: number
  warehouse_id: number
  material_id: number
  tx_type: string
  direction: number
  qty: string
  remark: string | null
}

type Warehouse = { id: number; name: string; code: string }
type Material = { id: number; name: string; code: string }

const balances = ref<Balance[]>([])
const txs = ref<Tx[]>([])
const warehouses = ref<Warehouse[]>([])
const materials = ref<Material[]>([])
const error = ref('')
const adjust = ref({
  warehouse_id: 0,
  material_id: 0,
  direction: 1,
  qty: '10',
  remark: '期初/调试调整',
})

async function load() {
  error.value = ''
  try {
    const [b, t, w, m] = await Promise.all([
      apiGet<{ items: Balance[] }>('/api/v1/inventory/balances'),
      apiGet<{ items: Tx[] }>('/api/v1/inventory/transactions'),
      apiGet<{ items: Warehouse[] }>('/api/v1/master/warehouses'),
      apiGet<{ items: Material[] }>('/api/v1/master/materials'),
    ])
    balances.value = b.data.items
    txs.value = t.data.items
    warehouses.value = w.data.items
    materials.value = m.data.items
    if (!adjust.value.warehouse_id && warehouses.value[0]) {
      adjust.value.warehouse_id = warehouses.value[0].id
    }
    if (!adjust.value.material_id && materials.value[0]) {
      adjust.value.material_id = materials.value[0].id
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

async function doAdjust() {
  error.value = ''
  try {
    await apiPost('/api/v1/inventory/adjust', {
      warehouse_id: Number(adjust.value.warehouse_id),
      material_id: Number(adjust.value.material_id),
      direction: Number(adjust.value.direction),
      qty: adjust.value.qty,
      remark: adjust.value.remark,
    })
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '调整失败'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <h1>库存</h1>
    <p>余额与流水查询；调试调整需 `inventory.adjust`。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h2>调试调整</h2>
      <div class="form-grid">
        <select v-model.number="adjust.warehouse_id">
          <option v-for="w in warehouses" :key="w.id" :value="w.id">
            {{ w.code }} - {{ w.name }}
          </option>
        </select>
        <select v-model.number="adjust.material_id">
          <option v-for="m in materials" :key="m.id" :value="m.id">
            {{ m.code }} - {{ m.name }}
          </option>
        </select>
        <select v-model.number="adjust.direction">
          <option :value="1">入库 (+1)</option>
          <option :value="-1">出库 (-1)</option>
        </select>
        <input v-model="adjust.qty" placeholder="数量" />
        <input v-model="adjust.remark" placeholder="备注" />
        <button type="button" @click="doAdjust">过账调整</button>
      </div>
    </div>

    <div class="card">
      <h2>库存余额</h2>
      <table>
        <thead>
          <tr>
            <th>仓库</th>
            <th>物料</th>
            <th>现存量</th>
            <th>可用量</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in balances" :key="idx">
            <td>{{ row.warehouse_name }}</td>
            <td>{{ row.material_code }} {{ row.material_name }}</td>
            <td>{{ row.qty_on_hand }}</td>
            <td>{{ row.qty_available }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>出入库流水</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>类型</th>
            <th>方向</th>
            <th>数量</th>
            <th>仓/料</th>
            <th>备注</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in txs" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.tx_type }}</td>
            <td>{{ row.direction }}</td>
            <td>{{ row.qty }}</td>
            <td>{{ row.warehouse_id }} / {{ row.material_id }}</td>
            <td>{{ row.remark || '-' }}</td>
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
