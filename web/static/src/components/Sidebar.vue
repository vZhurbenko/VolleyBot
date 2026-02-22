<template>
  <aside class="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
    <div class="p-6 border-b border-gray-800 flex items-center gap-3">
      <span class="text-3xl">🏐</span>
      <span class="text-xl font-bold">VolleyBot</span>
    </div>
    
    <nav class="flex-1 p-4 flex flex-col gap-2">
      <router-link to="/admin" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors" :class="{ 'bg-gray-800 text-white': $route.name === 'dashboard' }">
        <span class="text-xl">📊</span>
        <span class="font-medium">Дашборд</span>
      </router-link>
      <router-link to="/admin/template" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors" :class="{ 'bg-gray-800 text-white': $route.name === 'template' }">
        <span class="text-xl">📋</span>
        <span class="font-medium">Шаблон</span>
      </router-link>
      <router-link to="/admin/schedules" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors" :class="{ 'bg-gray-800 text-white': $route.name === 'schedules' }">
        <span class="text-xl">📅</span>
        <span class="font-medium">Расписания</span>
      </router-link>
      <router-link to="/admin/polls" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors" :class="{ 'bg-gray-800 text-white': $route.name === 'polls' }">
        <span class="text-xl">📈</span>
        <span class="font-medium">Опросы</span>
      </router-link>
      <router-link to="/admin/admins" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors" :class="{ 'bg-gray-800 text-white': $route.name === 'admins' }">
        <span class="text-xl">👥</span>
        <span class="font-medium">Админы</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup>
</script>
