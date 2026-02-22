<script setup>
import logo from '@/img/logo.svg'
</script>

<template>
  <aside class="w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col">
    <div class="p-6 border-b border-gray-200 flex items-center gap-3">
      <img :src="logo" alt="Team R Logo" class="w-10 h-10" />
      <span class="text-xl font-bold text-gray-900">Team R</span>
    </div>

    <nav class="flex-1 p-4 flex flex-col gap-2">
      <router-link to="/admin" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors" :class="{ 'bg-teal-50 text-teal-700': $route.name === 'dashboard' }">
        <span class="text-xl">📊</span>
        <span class="font-medium">Дашборд</span>
      </router-link>
      <router-link to="/admin/template" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors" :class="{ 'bg-teal-50 text-teal-700': $route.name === 'template' }">
        <span class="text-xl">📋</span>
        <span class="font-medium">Шаблон</span>
      </router-link>
      <router-link to="/admin/schedules" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors" :class="{ 'bg-teal-50 text-teal-700': $route.name === 'schedules' }">
        <span class="text-xl">📅</span>
        <span class="font-medium">Расписания</span>
      </router-link>
      <router-link to="/admin/polls" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors" :class="{ 'bg-teal-50 text-teal-700': $route.name === 'polls' }">
        <span class="text-xl">📈</span>
        <span class="font-medium">Опросы</span>
      </router-link>
      <router-link to="/admin/admins" class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors" :class="{ 'bg-teal-50 text-teal-700': $route.name === 'admins' }">
        <span class="text-xl">👥</span>
        <span class="font-medium">Админы</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup>
</script>
