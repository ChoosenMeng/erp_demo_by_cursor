<script setup lang="ts"></script>

<template>
  <section class="home">
    <p class="eyebrow">Cursor ERP Demo · M0</p>
    <h1>脚手架已就绪</h1>
    <p class="lead">
      后端 FastAPI + 前端 Vue3 已分离部署，数据库使用本机 MySQL（erp_demo）。下一阶段接入组织权限与业务模块。
    </p>
    <div class="actions">
      <RouterLink class="primary" to="/health">检查后端健康状态</RouterLink>
      <a class="secondary" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
        打开 API 文档
      </a>
    </div>
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
  line-height: 1.2;
}

.lead {
  margin: 0 0 1.5rem;
  color: #4b5c5b;
  line-height: 1.6;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.primary,
.secondary {
  display: inline-flex;
  align-items: center;
  padding: 0.7rem 1rem;
  border-radius: 0.6rem;
  text-decoration: none;
  font-weight: 600;
}

.primary {
  background: #0f766e;
  color: #fff;
}

.secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #1c2b2a;
  border: 1px solid rgba(28, 43, 42, 0.12);
}
</style>
