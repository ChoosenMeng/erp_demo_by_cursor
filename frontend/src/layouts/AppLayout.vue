<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPreferredCompanyId, useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const companies = computed(() => auth.companies.value)
const activeCompany = computed(() => auth.activeCompany.value)
const selectedCompanyId = ref<number | null>(
  getPreferredCompanyId() ?? auth.user.value?.company_id ?? null,
)
const switching = ref(false)

watch(
  () => [auth.user.value?.company_id, companies.value.length] as const,
  () => {
    selectedCompanyId.value =
      getPreferredCompanyId() ?? auth.user.value?.company_id ?? null
  },
  { immediate: true },
)

type NavItem = {
  to: string
  label: string
  permission?: string
}

const allNav: NavItem[] = [
  { to: '/', label: '首页' },
  { to: '/health', label: '健康检查' },
  { to: '/companies', label: '公司', permission: 'org.company.read' },
  { to: '/users', label: '用户', permission: 'org.user.read' },
  { to: '/roles', label: '角色权限', permission: 'org.role.read' },
  { to: '/customers', label: '客户', permission: 'master.read' },
  { to: '/suppliers', label: '供应商', permission: 'master.read' },
  { to: '/materials', label: '物料', permission: 'master.read' },
  { to: '/warehouses', label: '仓库', permission: 'master.read' },
  { to: '/inventory', label: '库存', permission: 'inventory.read' },
  { to: '/purchase', label: '采购', permission: 'purchase.read' },
  { to: '/sales', label: '销售', permission: 'sales.read' },
  { to: '/finance', label: '财务', permission: 'finance.read' },
  { to: '/dashboard', label: '仪表盘', permission: 'dashboard.read' },
]

const navItems = computed(() =>
  allNav.filter((item) => !item.permission || auth.hasPermission(item.permission)),
)

const entityKey = computed(
  () => selectedCompanyId.value ?? activeCompany.value?.id ?? 'none',
)

function isActive(path: string) {
  return route.path === path
}

async function onCompanyChange(event: Event) {
  const nextId = Number((event.target as HTMLSelectElement).value)
  if (!Number.isFinite(nextId) || nextId <= 0) return
  if (nextId === getPreferredCompanyId()) return

  switching.value = true
  try {
    await auth.switchCompany(nextId)
    selectedCompanyId.value = nextId
    // Remount current function module under new entity (no full reload)
    await router.replace({
      path: route.path,
      query: { ...route.query },
      hash: route.hash,
    })
  } catch (err) {
    selectedCompanyId.value = getPreferredCompanyId() ?? auth.user.value?.company_id ?? null
    window.alert(err instanceof Error ? err.message : '切换公司失败')
  } finally {
    switching.value = false
  }
}

async function onLogout() {
  await auth.logout()
  await router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">ERP</span>
        <div>
          <strong>Cursor ERP</strong>
          <p>Demo Console</p>
        </div>
      </div>
      <nav>
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: isActive(item.to) }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <div class="main">
      <header class="topbar">
        <div class="company-switch">
          <span class="muted">当前公司（Entity，优先于功能模块）</span>
          <div class="entity-row">
            <select
              class="entity-select"
              :value="selectedCompanyId ?? ''"
              :disabled="switching || companies.length === 0"
              @change="onCompanyChange"
            >
              <option v-if="companies.length === 0" value="" disabled>
                未加载到公司，请重新登录
              </option>
              <option v-for="c in companies" :key="c.id" :value="c.id">
                {{ c.name }} · {{ c.code }} · {{ c.base_currency_code }}
              </option>
            </select>
            <span v-if="activeCompany" class="entity-badge">
              {{ activeCompany.code }} / {{ activeCompany.base_currency_code }}
            </span>
          </div>
        </div>
        <div class="user">
          <span>{{ auth.user.value?.display_name ?? '未登录' }}</span>
          <button type="button" @click="onLogout">退出</button>
        </div>
      </header>
      <main class="content">
        <!-- key by entity so module pages remount when company changes -->
        <RouterView :key="String(entityKey)" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 40%),
    linear-gradient(160deg, #f3f6f4 0%, #e8eef0 45%, #f7f4ef 100%);
  color: #1c2b2a;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.sidebar {
  padding: 1.5rem 1rem;
  border-right: 1px solid rgba(28, 43, 42, 0.08);
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(8px);
}

.brand {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 2rem;
  padding: 0 0.5rem;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  background: #0f766e;
  color: #fff;
  font-weight: 700;
}

.brand p {
  margin: 0.15rem 0 0;
  font-size: 0.8rem;
  color: #5b6b6a;
}

.nav-link {
  display: block;
  padding: 0.65rem 0.85rem;
  margin-bottom: 0.35rem;
  border-radius: 0.55rem;
  color: #314241;
  text-decoration: none;
}

.nav-link:hover {
  background: rgba(15, 118, 110, 0.08);
}

.nav-link.active {
  background: #0f766e;
  color: #fff;
}

.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 2rem;
  border-bottom: 1px solid rgba(28, 43, 42, 0.08);
  background: rgba(255, 255, 255, 0.55);
}

.muted {
  display: block;
  color: #5b6b6a;
  font-size: 0.75rem;
}

.entity-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.25rem;
}

.entity-select {
  min-width: min(420px, 70vw);
  padding: 0.5rem 0.65rem;
  border-radius: 0.45rem;
  border: 1px solid rgba(15, 118, 110, 0.35);
  font: inherit;
  font-weight: 600;
  background: #fff;
  color: #0f766e;
}

.entity-badge {
  display: inline-flex;
  padding: 0.3rem 0.55rem;
  border-radius: 0.4rem;
  background: rgba(15, 118, 110, 0.12);
  color: #0f766e;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
}

.user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.user button {
  border: 0;
  border-radius: 0.45rem;
  padding: 0.4rem 0.7rem;
  background: #0f766e;
  color: #fff;
  cursor: pointer;
}

.content {
  padding: 2rem;
}

@media (max-width: 800px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .entity-select {
    min-width: 0;
    width: 100%;
  }
}
</style>
