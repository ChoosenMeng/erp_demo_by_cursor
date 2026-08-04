<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet } from '../api/client'

type HealthData = {
  status: string
  app: string
  env: string
  database: {
    status: string
    name: string | null
    version: string | null
  }
}

const loading = ref(true)
const error = ref<string | null>(null)
const data = ref<HealthData | null>(null)

async function load() {
  loading.value = true
  error.value = null
  try {
    const result = await apiGet<HealthData>('/api/v1/health')
    data.value = result.data
  } catch (err) {
    error.value = err instanceof Error ? err.message : '请求失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="health">
    <h1>健康检查</h1>
    <p>请求后端接口 <code>/api/v1/health</code>（经 Vite 代理），含 MySQL 连通性。</p>

    <button class="refresh" type="button" :disabled="loading" @click="load">重新检查</button>

    <div v-if="loading" class="card">加载中…</div>
    <div v-else-if="error" class="card error">
      <strong>无法连接后端</strong>
      <p>{{ error }}</p>
      <p>
        请先：
        <code>conda activate cursor-erp-demo</code>
        ，再在 backend 目录执行
        <code>uvicorn app.main:app --reload</code>
      </p>
    </div>
    <div v-else-if="data" class="card" :class="data.status === 'healthy' ? 'ok' : 'warn'">
      <strong>应用状态：{{ data.status }}</strong>
      <ul>
        <li>应用：{{ data.app }}</li>
        <li>环境：{{ data.env }}</li>
        <li>数据库状态：{{ data.database.status }}</li>
        <li>数据库名：{{ data.database.name ?? '-' }}</li>
        <li>数据库版本：{{ data.database.version ?? '-' }}</li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
h1 {
  margin: 0 0 0.5rem;
}

p {
  color: #4b5c5b;
}

code {
  padding: 0.1rem 0.35rem;
  border-radius: 0.3rem;
  background: rgba(15, 118, 110, 0.1);
}

.refresh {
  margin-top: 0.75rem;
  padding: 0.45rem 0.85rem;
  border: 1px solid rgba(15, 118, 110, 0.35);
  border-radius: 0.5rem;
  background: #fff;
  color: #0f766e;
  font-weight: 600;
  cursor: pointer;
}

.refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.card {
  margin-top: 1.25rem;
  max-width: 36rem;
  padding: 1rem 1.1rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(28, 43, 42, 0.08);
}

.card ul {
  margin: 0.75rem 0 0;
  padding-left: 1.1rem;
}

.card.ok {
  border-color: rgba(15, 118, 110, 0.35);
}

.card.warn {
  border-color: rgba(180, 120, 20, 0.45);
}

.card.error {
  border-color: rgba(185, 28, 28, 0.35);
  color: #7f1d1d;
}
</style>
