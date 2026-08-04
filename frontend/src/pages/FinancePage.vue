<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost } from '../api/client'

type ApBill = {
  id: number
  doc_no: string
  supplier_name: string | null
  amount: string
  paid_amount: string
  status: string
}

type ArBill = {
  id: number
  doc_no: string
  customer_name: string | null
  amount: string
  received_amount: string
  status: string
}

const apItems = ref<ApBill[]>([])
const arItems = ref<ArBill[]>([])
const error = ref('')
const payAmount = ref<Record<number, string>>({})
const recvAmount = ref<Record<number, string>>({})

async function load() {
  error.value = ''
  try {
    const [ap, ar] = await Promise.all([
      apiGet<{ items: ApBill[] }>('/api/v1/finance/ap-bills'),
      apiGet<{ items: ArBill[] }>('/api/v1/finance/ar-bills'),
    ])
    apItems.value = ap.data.items
    arItems.value = ar.data.items
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

async function pay(id: number) {
  error.value = ''
  try {
    await apiPost(`/api/v1/finance/ap-bills/${id}/payments`, {
      amount: payAmount.value[id] || '0',
      pay_date: new Date().toISOString().slice(0, 10),
      remark: '页面付款',
    })
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '付款失败'
  }
}

async function receive(id: number) {
  error.value = ''
  try {
    await apiPost(`/api/v1/finance/ar-bills/${id}/receipts`, {
      amount: recvAmount.value[id] || '0',
      pay_date: new Date().toISOString().slice(0, 10),
      remark: '页面收款',
    })
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '收款失败'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <h1>财务</h1>
    <p>入库生成应付、出库生成应收；可登记收付款。权限：`finance.read` / `finance.write`。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h2>应付</h2>
      <table>
        <thead>
          <tr>
            <th>单号</th>
            <th>供应商</th>
            <th>金额</th>
            <th>已付</th>
            <th>状态</th>
            <th>付款</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in apItems" :key="row.id">
            <td>{{ row.doc_no }}</td>
            <td>{{ row.supplier_name || '-' }}</td>
            <td>{{ row.amount }}</td>
            <td>{{ row.paid_amount }}</td>
            <td>{{ row.status }}</td>
            <td class="ops">
              <input v-model="payAmount[row.id]" placeholder="金额" />
              <button type="button" @click="pay(row.id)">付款</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>应收</h2>
      <table>
        <thead>
          <tr>
            <th>单号</th>
            <th>客户</th>
            <th>金额</th>
            <th>已收</th>
            <th>状态</th>
            <th>收款</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in arItems" :key="row.id">
            <td>{{ row.doc_no }}</td>
            <td>{{ row.customer_name || '-' }}</td>
            <td>{{ row.amount }}</td>
            <td>{{ row.received_amount }}</td>
            <td>{{ row.status }}</td>
            <td class="ops">
              <input v-model="recvAmount[row.id]" placeholder="金额" />
              <button type="button" @click="receive(row.id)">收款</button>
            </td>
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
.ops {
  display: flex;
  gap: 0.4rem;
}
input,
button {
  padding: 0.45rem 0.55rem;
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
