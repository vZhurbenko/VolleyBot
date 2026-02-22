<template>
  <aside class="w-64 bg-gray-900 text-white min-h-screen flex flex-col">
    <div class="p-6 border-b border-gray-800 flex items-center gap-3">
      <span class="text-3xl">🏐</span>
      <span class="text-xl font-bold">VolleyBot</span>
    </div>
    
    <nav class="flex-1 p-4 space-y-2">
      <a href="/admin" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors" :class="{ 'bg-gray-800 text-white': $route.path === '/admin' }">
        <span class="text-xl">📊</span>
        <span class="font-medium">Дашборд</span>
      </a>
      <a href="#template" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors">
        <span class="text-xl">📋</span>
        <span class="font-medium">Шаблон</span>
      </a>
      <a href="#schedules" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors">
        <span class="text-xl">📅</span>
        <span class="font-medium">Расписания</span>
      </a>
      <a href="#polls" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors">
        <span class="text-xl">📈</span>
        <span class="font-medium">Опросы</span>
      </a>
      <a href="#admins" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 hover:text-white transition-colors">
        <span class="text-xl">👥</span>
        <span class="font-medium">Админы</span>
      </a>
    </nav>
  </aside>
</template>

<script setup>
</script>
