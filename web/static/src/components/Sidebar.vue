<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="logo">🏐</span>
      <span class="logo-text">VolleyBot</span>
    </div>
    
    <nav class="sidebar-nav">
      <a href="/admin" class="nav-item" :class="{ active: $route.path === '/admin' }">
        <span class="nav-icon">📊</span>
        <span class="nav-text">Дашборд</span>
      </a>
      <a href="#template" class="nav-item" :class="{ active: $route.path === '/admin/template' }">
        <span class="nav-icon">📋</span>
        <span class="nav-text">Шаблон</span>
      </a>
      <a href="#schedules" class="nav-item" :class="{ active: $route.path === '/admin/schedules' }">
        <span class="nav-icon">📅</span>
        <span class="nav-text">Расписания</span>
      </a>
      <a href="#polls" class="nav-item" :class="{ active: $route.path === '/admin/polls' }">
        <span class="nav-icon">📈</span>
        <span class="nav-text">Опросы</span>
      </a>
      <a href="#admins" class="nav-item" :class="{ active: $route.path === '/admin/admins' }">
        <span class="nav-icon">👥</span>
        <span class="nav-text">Админы</span>
      </a>
    </nav>
  </aside>
</template>

<script setup>
</script>

<style scoped>
.sidebar {
  @apply w-64 bg-gray-900 text-white min-h-screen flex flex-col;
}

.sidebar-header {
  @apply p-6 border-b border-gray-800 flex items-center gap-3;
}

.logo {
  @apply text-3xl;
}

.logo-text {
  @apply text-xl font-bold;
}

.sidebar-nav {
  @apply flex-1 p-4 space-y-2;
}

.nav-item {
  @apply flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors;
}

.nav-item.active {
  @apply bg-gray-800 text-white;
}

.nav-icon {
  @apply text-xl;
}

.nav-text {
  @apply font-medium;
}
</style>
