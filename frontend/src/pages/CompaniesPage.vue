<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost } from '../api/client'

type CompanyRow = {
  id: number
  code: string
  name: string
  base_currency_code: string
  status: string
}

const items = ref<CompanyRow[]>([])
const error = ref('')
const form = ref({
  code: '',
  name: '',
  base_currency_code: 'CNY',
  status: 'active',
})

async function load() {
  error.value = ''
  try {
    const res = await apiGet<{ items: CompanyRow[] }>('/api/v1/org/companies')
    items.value = res.data.items
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

async function createCompany() {
  error.value = ''
  try {
    await apiPost('/api/v1/org/companies', form.value)
    form.value = { code: '', name: '', base_currency_code: 'CNY', status: 'active' }
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '创建失败'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <h1>公司管理</h1>
    <p>需要权限 `org.company.read` / `org.company.write`。当前公司上下文来自 Header `X-Company-Id`。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h2>新建公司</h2>
      <div class="form-grid">
        <input v-model="form.code" placeholder="编码" />
        <input v-model="form.name" placeholder="名称" />
        <input v-model="form.base_currency_code" placeholder="本位币" />
        <button type="button" @click="createCompany">创建</button>
      </div>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>编码</th>
            <th>名称</th>
            <th>本位币</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in items" :key="c.id">
            <td>{{ c.id }}</td>
            <td>{{ c.code }}</td>
            <td>{{ c.name }}</td>
            <td>{{ c.base_currency_code }}</td>
            <td>{{ c.status }}</td>
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
