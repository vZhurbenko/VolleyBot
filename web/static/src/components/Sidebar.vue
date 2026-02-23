<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import logo from '@/img/logo.svg'

const isOpen = ref(false)

const handleToggleMenu = () => {
  isOpen.value = !isOpen.value
}

onMounted(() => {
  window.addEventListener('toggle-menu', handleToggleMenu)
})

onUnmounted(() => {
  window.removeEventListener('toggle-menu', handleToggleMenu)
})
</script>

<template>
  <!-- Overlay для мобильных -->
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/50 z-40 lg:hidden"
    @click="isOpen = false"
  ></div>

  <!-- Sidebar -->
  <aside
    :class="[
      'fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 min-h-screen flex flex-col transform transition-transform duration-300 lg:transform-none',
      isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
    ]"
  >
    <div class="p-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <img :src="logo" alt="Team R Logo" class="w-10 h-10" />
        <span class="text-xl font-bold text-gray-900">Team R</span>
      </div>
      <!-- Кнопка закрытия для мобильных -->
      <button
        @click="isOpen = false"
        class="lg:hidden p-2 rounded hover:bg-gray-100"
      >
        ✕
      </button>
    </div>

    <nav class="flex-1 px-4 pb-4 flex flex-col gap-2">
      <router-link
        to="/admin"
        class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
        :class="{ 'bg-teal-50 text-teal-700': $route.name === 'dashboard' }"
        @click="isOpen = false"
      >
        <span class="text-xl">📊</span>
        <span class="font-medium">Дашборд</span>
      </router-link>
      <router-link
        to="/admin/template"
        class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
        :class="{ 'bg-teal-50 text-teal-700': $route.name === 'template' }"
        @click="isOpen = false"
      >
        <span class="text-xl">📋</span>
        <span class="font-medium">Шаблон</span>
      </router-link>
      <router-link
        to="/admin/schedules"
        class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
        :class="{ 'bg-teal-50 text-teal-700': $route.name === 'schedules' }"
        @click="isOpen = false"
      >
        <span class="text-xl">📅</span>
        <span class="font-medium">Расписания</span>
      </router-link>
      <router-link
        to="/admin/polls"
        class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
        :class="{ 'bg-teal-50 text-teal-700': $route.name === 'polls' }"
        @click="isOpen = false"
      >
        <span class="text-xl">📈</span>
        <span class="font-medium">Опросы</span>
      </router-link>
      <router-link
        to="/admin/admins"
        class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
        :class="{ 'bg-teal-50 text-teal-700': $route.name === 'admins' }"
        @click="isOpen = false"
      >
        <span class="text-xl">👥</span>
        <span class="font-medium">Админы</span>
      </router-link>
    </nav>
  </aside>
</template>
