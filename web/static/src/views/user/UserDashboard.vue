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

    <!-- Мои тренировки -->
    <div id="my-trainings">
      <MyTrainingsCard />
    </div>

    <!-- Календарь тренировок -->
    <div id="calendar" class="bg-white rounded shadow p-4 lg:p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Календарь тренировок</h2>
      <Calendar />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Calendar from '@/components/Calendar.vue'
import MyTrainingsCard from '@/components/MyTrainingsCard.vue'

const authStore = useAuthStore()

onMounted(async () => {
  await authStore.loadUser()
})
</script>
