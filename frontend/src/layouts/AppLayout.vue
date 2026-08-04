<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { to: '/', label: '首页' },
  { to: '/health', label: '健康检查' },
]

function isActive(path: string) {
  return route.path === path
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
    <main class="content">
      <RouterView />
    </main>
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
  letter-spacing: 0.04em;
}

.brand strong {
  display: block;
  font-size: 1rem;
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
  transition: background 0.2s ease, color 0.2s ease;
}

.nav-link:hover {
  background: rgba(15, 118, 110, 0.08);
}

.nav-link.active {
  background: #0f766e;
  color: #fff;
}

.content {
  padding: 2rem;
}

@media (max-width: 800px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid rgba(28, 43, 42, 0.08);
  }
}
</style>
