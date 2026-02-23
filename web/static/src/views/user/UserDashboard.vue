<template>
  <div class="flex flex-col gap-4 lg:gap-6">
    <!-- Приветствие -->
    <div class="bg-white rounded shadow p-4 lg:p-6">
      <h1 class="text-2xl font-bold text-gray-900">
        Привет, {{ authStore.user?.first_name || 'Пользователь' }}! 👋
      </h1>
      <p class="text-gray-500 mt-1">
        Управляйте своими записями на тренировки
      </p>
    </div>

    <!-- Быстрые действия -->
    <div class="bg-white rounded shadow p-4 lg:p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <router-link
          to="/user/calendar"
          class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors"
        >
          <div class="w-10 h-10 rounded bg-teal-100 flex items-center justify-center text-xl">
            📅
          </div>
          <div>
            <p class="font-medium text-gray-900">Записаться на тренировку</p>
            <p class="text-sm text-gray-500">Выбрать дату и время</p>
          </div>
        </router-link>

        <router-link
          to="/user/my-trainings"
          class="flex items-center gap-4 p-4 rounded border border-gray-200 hover:border-teal-300 hover:bg-teal-50 transition-colors"
        >
          <div class="w-10 h-10 rounded bg-teal-100 flex items-center justify-center text-xl">
            📝
          </div>
          <div>
            <p class="font-medium text-gray-900">Мои записи</p>
            <p class="text-sm text-gray-500">Просмотр всех записей</p>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(async () => {
  await authStore.loadUser()
})
</script>
