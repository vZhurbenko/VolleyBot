<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import logo from '@/img/logo.svg'

const authStore = useAuthStore()

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
      <!-- Меню для администраторов -->
      <template v-if="authStore.isAdmin">
        <router-link
          to="/dashboard"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'dashboard' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📊</span>
          <span class="font-medium">Дашборд</span>
        </router-link>
        <router-link
          to="/dashboard/calendar"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'calendar' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📅</span>
          <span class="font-medium">Календарь</span>
        </router-link>
        <router-link
          to="/dashboard/my-trainings"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'my-trainings' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📝</span>
          <span class="font-medium">Мои тренировки</span>
        </router-link>
        <router-link
          to="/dashboard/schedules"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'schedules' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📋</span>
          <span class="font-medium">Расписания</span>
        </router-link>
        <router-link
          to="/dashboard/users"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'users' }"
          @click="isOpen = false"
        >
          <span class="text-xl">👥</span>
          <span class="font-medium">Пользователи</span>
        </router-link>
        <router-link
          to="/dashboard/invites"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'invites' }"
          @click="isOpen = false"
        >
          <span class="text-xl">🔗</span>
          <span class="font-medium">Приглашения</span>
        </router-link>
        <router-link
          to="/dashboard/trainings"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'trainings' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📝</span>
          <span class="font-medium">Записи</span>
        </router-link>
        <router-link
          to="/dashboard/template"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'template' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📄</span>
          <span class="font-medium">Шаблон</span>
        </router-link>
      </template>

      <!-- Меню для обычных пользователей -->
      <template v-else>
        <router-link
          to="/dashboard/calendar"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'calendar' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📅</span>
          <span class="font-medium">Календарь</span>
        </router-link>
        <router-link
          to="/dashboard/my-trainings"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'my-trainings' }"
          @click="isOpen = false"
        >
          <span class="text-xl">📝</span>
          <span class="font-medium">Мои тренировки</span>
        </router-link>
      </template>
    </nav>
  </aside>
</template>
