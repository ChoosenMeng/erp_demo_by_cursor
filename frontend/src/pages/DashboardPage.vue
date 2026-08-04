<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiGet } from '../api/client'

type Summary = {
  sales_amount_today: string
  sales_amount_month: string
  purchase_amount_month: string
  inventory_sku_count: number
  pending_so_count: number
  pending_po_count: number
}

type Trend = { points: { date: string; amount: string }[] }

const summary = ref<Summary | null>(null)
const trend = ref<Trend | null>(null)
const error = ref('')

const maxAmount = computed(() => {
  const pts = trend.value?.points ?? []
  return Math.max(...pts.map((p) => Number(p.amount) || 0), 1)
})

async function load() {
  error.value = ''
  try {
    const [s, t] = await Promise.all([
      apiGet<Summary>('/api/v1/dashboard/summary'),
      apiGet<Trend>('/api/v1/dashboard/sales-trend?days=7'),
    ])
    summary.value = s.data
    trend.value = t.data
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <h1>仪表盘</h1>
    <p>指标来自真实订单/库存/财务数据。权限：`dashboard.read`。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="summary" class="metrics">
      <div>
        <span>今日销售额</span>
        <strong>{{ summary.sales_amount_today }}</strong>
      </div>
      <div>
        <span>本月销售额</span>
        <strong>{{ summary.sales_amount_month }}</strong>
      </div>
      <div>
        <span>本月采购额</span>
        <strong>{{ summary.purchase_amount_month }}</strong>
      </div>
      <div>
        <span>库存 SKU</span>
        <strong>{{ summary.inventory_sku_count }}</strong>
      </div>
      <div>
        <span>待办销售单</span>
        <strong>{{ summary.pending_so_count }}</strong>
      </div>
      <div>
        <span>待办采购单</span>
        <strong>{{ summary.pending_po_count }}</strong>
      </div>
    </div>

    <div class="card">
      <h2>近 7 日销售趋势</h2>
      <div class="bars">
        <div v-for="p in trend?.points ?? []" :key="p.date" class="bar-col">
          <div
            class="bar"
            :style="{ height: `${(Number(p.amount) / maxAmount) * 120}px` }"
            :title="p.amount"
          />
          <span>{{ p.date.slice(5) }}</span>
        </div>
      </div>
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
.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}
.metrics > div {
  padding: 0.9rem 1rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(28, 43, 42, 0.08);
}
.metrics span {
  display: block;
  color: #5b6b6a;
  font-size: 0.8rem;
}
.metrics strong {
  display: block;
  margin-top: 0.35rem;
  font-size: 1.25rem;
}
.card {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(28, 43, 42, 0.08);
}
.bars {
  display: flex;
  align-items: flex-end;
  gap: 0.65rem;
  min-height: 160px;
  padding-top: 1rem;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
}
.bar {
  width: 100%;
  max-width: 36px;
  min-height: 2px;
  border-radius: 0.35rem 0.35rem 0 0;
  background: #0f766e;
}
.bar-col span {
  font-size: 0.75rem;
  color: #5b6b6a;
}
</style>
