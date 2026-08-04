<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost } from '../api/client'

type UserRow = {
  id: number
  username: string
  display_name: string
  email: string | null
  status: string
  roles: string[]
}

type RoleRow = { id: number; code: string; name: string }
type CompanyRow = { id: number; code: string; name: string }

const items = ref<UserRow[]>([])
const roles = ref<RoleRow[]>([])
const companies = ref<CompanyRow[]>([])
const error = ref('')
const loading = ref(false)

const form = ref({
  username: '',
  password: '',
  display_name: '',
  role_id: null as number | null,
  company_id: null as number | null,
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [usersRes, rolesRes, companiesRes] = await Promise.all([
      apiGet<{ items: UserRow[] }>('/api/v1/org/users'),
      apiGet<RoleRow[]>('/api/v1/org/roles'),
      apiGet<{ items: CompanyRow[] }>('/api/v1/org/companies'),
    ])
    items.value = usersRes.data.items
    roles.value = rolesRes.data
    companies.value = companiesRes.data.items
    if (!form.value.role_id && roles.value.length) form.value.role_id = roles.value[0].id
    if (!form.value.company_id && companies.value.length) {
      form.value.company_id = companies.value[0].id
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function createUser() {
  error.value = ''
  try {
    await apiPost('/api/v1/org/users', {
      username: form.value.username,
      password: form.value.password,
      display_name: form.value.display_name,
      role_ids: form.value.role_id ? [form.value.role_id] : [],
      company_ids: form.value.company_id ? [form.value.company_id] : [],
      default_company_id: form.value.company_id,
    })
    form.value.username = ''
    form.value.password = ''
    form.value.display_name = ''
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
    <h1>用户管理</h1>
    <p>需要权限 `org.user.read` / `org.user.write`。</p>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading">加载中…</p>

    <div class="card">
      <h2>新建用户</h2>
      <div class="form-grid">
        <input v-model="form.username" placeholder="用户名" />
        <input v-model="form.password" type="password" placeholder="密码" />
        <input v-model="form.display_name" placeholder="显示名" />
        <select v-model.number="form.role_id">
          <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.name }} ({{ r.code }})</option>
        </select>
        <select v-model.number="form.company_id">
          <option v-for="c in companies" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <button type="button" @click="createUser">创建</button>
      </div>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>显示名</th>
            <th>状态</th>
            <th>角色</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in items" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.display_name }}</td>
            <td>{{ u.status }}</td>
            <td>{{ u.roles.join(', ') }}</td>
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
