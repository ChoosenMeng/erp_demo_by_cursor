<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('admin')
const password = ref('admin123')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (err) {
    error.value = err instanceof Error ? err.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <form class="panel" @submit.prevent="onSubmit">
      <p class="eyebrow">Cursor ERP</p>
      <h1>登录</h1>
      <p class="hint">默认账号 admin / admin123（开发环境）</p>

      <label>
        用户名
        <input v-model="username" autocomplete="username" required />
      </label>
      <label>
        密码
        <input v-model="password" type="password" autocomplete="current-password" required />
      </label>

      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">{{ loading ? '登录中…' : '登录' }}</button>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at top left, rgba(15, 118, 110, 0.14), transparent 40%),
    linear-gradient(160deg, #f3f6f4 0%, #e8eef0 45%, #f7f4ef 100%);
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.panel {
  width: min(420px, calc(100vw - 2rem));
  padding: 1.75rem;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(28, 43, 42, 0.08);
  display: grid;
  gap: 0.85rem;
}

.eyebrow {
  margin: 0;
  color: #0f766e;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.8rem;
}

h1 {
  margin: 0;
}

.hint {
  margin: 0;
  color: #5b6b6a;
  font-size: 0.9rem;
}

label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.9rem;
  color: #314241;
}

input {
  padding: 0.65rem 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(28, 43, 42, 0.18);
  font: inherit;
}

button {
  margin-top: 0.35rem;
  padding: 0.75rem 1rem;
  border: 0;
  border-radius: 0.55rem;
  background: #0f766e;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.error {
  margin: 0;
  color: #b91c1c;
  font-size: 0.9rem;
}
</style>
