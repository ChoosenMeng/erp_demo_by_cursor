<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiGet, apiPost, apiPut } from '../api/client'

type RoleRow = {
  id: number
  code: string
  name: string
  description: string | null
  permission_codes: string[]
}

type PermRow = { id: number; code: string; name: string; module: string }

const roles = ref<RoleRow[]>([])
const permissions = ref<PermRow[]>([])
const error = ref('')
const selectedRoleId = ref<number | null>(null)
const selectedPermIds = ref<number[]>([])

const form = ref({ code: '', name: '', description: '' })

async function load() {
  error.value = ''
  try {
    const [rolesRes, permRes] = await Promise.all([
      apiGet<RoleRow[]>('/api/v1/org/roles'),
      apiGet<PermRow[]>('/api/v1/org/permissions'),
    ])
    roles.value = rolesRes.data
    permissions.value = permRes.data
    if (roles.value.length && selectedRoleId.value == null) {
      selectRole(roles.value[0])
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  }
}

function selectRole(role: RoleRow) {
  selectedRoleId.value = role.id
  selectedPermIds.value = permissions.value
    .filter((p) => role.permission_codes.includes(p.code))
    .map((p) => p.id)
}

async function createRole() {
  error.value = ''
  try {
    await apiPost('/api/v1/org/roles', form.value)
    form.value = { code: '', name: '', description: '' }
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '创建失败'
  }
}

async function savePermissions() {
  if (selectedRoleId.value == null) return
  error.value = ''
  try {
    await apiPut(`/api/v1/org/roles/${selectedRoleId.value}/permissions`, {
      permission_ids: selectedPermIds.value,
    })
    await load()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '保存失败'
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page">
    <h1>角色与权限</h1>
    <p>需要权限 `org.role.read` / `org.role.write`。</p>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h2>新建角色</h2>
      <div class="form-grid">
        <input v-model="form.code" placeholder="编码" />
        <input v-model="form.name" placeholder="名称" />
        <input v-model="form.description" placeholder="说明" />
        <button type="button" @click="createRole">创建</button>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h2>角色列表</h2>
        <button
          v-for="r in roles"
          :key="r.id"
          type="button"
          class="role-btn"
          :class="{ active: selectedRoleId === r.id }"
          @click="selectRole(r)"
        >
          {{ r.name }} ({{ r.code }})
        </button>
      </div>

      <div class="card">
        <h2>绑定权限</h2>
        <label v-for="p in permissions" :key="p.id" class="perm">
          <input v-model="selectedPermIds" type="checkbox" :value="p.id" />
          <span>{{ p.code }} — {{ p.name }}</span>
        </label>
        <button type="button" class="save" @click="savePermissions">保存权限</button>
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
.grid {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 1rem;
}
@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }
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
.role-btn {
  display: block;
  width: 100%;
  text-align: left;
  margin-bottom: 0.4rem;
  background: rgba(15, 118, 110, 0.08);
  color: #1c2b2a;
}
.role-btn.active {
  background: #0f766e;
  color: #fff;
}
.perm {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin: 0.35rem 0;
}
.save {
  margin-top: 0.75rem;
}
</style>
