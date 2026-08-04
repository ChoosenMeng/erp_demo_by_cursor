<script setup lang="ts">
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
</script>

<template>
  <section class="home">
    <p class="eyebrow">Cursor ERP Demo · M1</p>
    <h1>欢迎，{{ auth.user.value?.display_name ?? '访客' }}</h1>
    <p class="lead">
      已完成组织权限基础能力：登录鉴权、公司上下文、用户/角色管理。可从左侧菜单进入各模块。
    </p>
    <ul>
      <li>角色：{{ (auth.user.value?.roles ?? []).join(', ') || '-' }}</li>
      <li>权限：{{ (auth.user.value?.permissions ?? []).join(', ') || '-' }}</li>
      <li>当前公司 ID：{{ auth.user.value?.company_id ?? '-' }}</li>
    </ul>
  </section>
</template>

<style scoped>
.home {
  max-width: 42rem;
}
.eyebrow {
  margin: 0 0 0.75rem;
  color: #0f766e;
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 {
  margin: 0 0 0.75rem;
  font-size: clamp(1.8rem, 3vw, 2.4rem);
}
.lead {
  margin: 0 0 1rem;
  color: #4b5c5b;
  line-height: 1.6;
}
ul {
  margin: 0;
  padding-left: 1.1rem;
  color: #314241;
  line-height: 1.8;
}
</style>
