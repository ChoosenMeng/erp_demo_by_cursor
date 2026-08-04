<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost } from '../api/client'

type Row = {
  id: number
  code: string
  name: string
  spec: string | null
  uom: string
  material_type: string
  status: string
}

const items = ref<Row[]>([])
const error = ref('')
const form = ref({
  code: '',
  name: '',
  spec: '',
  uom: 'pcs',
  material_type: 'finished',
  status: 'active',
})

async function load() {
  error.value = ''
  try {
    const res = await apiGet<{ items: Row[] }>('/api/v1/master/materials')
    items.value = res.data.items
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

async function createRow() {
  error.value = ''
  try {
    await apiPost('/api/v1/master/materials', {
      ...form.value,
      spec: form.value.spec || null,
    })
    form.value = {
      code: '',
      name: '',
      spec: '',
      uom: 'pcs',
      material_type: 'finished',
      status: 'active',
    }
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
    <h1>物料</h1>
    <p>类型：finished / raw / other。权限：`master.read` / `master.write`。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h2>新建物料</h2>
      <div class="form-grid">
        <input v-model="form.code" placeholder="编码" />
        <input v-model="form.name" placeholder="名称" />
        <input v-model="form.spec" placeholder="规格" />
        <input v-model="form.uom" placeholder="单位" />
        <select v-model="form.material_type">
          <option value="finished">成品</option>
          <option value="raw">原材料</option>
          <option value="other">其他</option>
        </select>
        <button type="button" @click="createRow">创建</button>
      </div>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>编码</th>
            <th>名称</th>
            <th>规格</th>
            <th>单位</th>
            <th>类型</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in items" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.code }}</td>
            <td>{{ row.name }}</td>
            <td>{{ row.spec || '-' }}</td>
            <td>{{ row.uom }}</td>
            <td>{{ row.material_type }}</td>
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
