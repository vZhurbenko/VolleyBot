<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-900">Мои тренировки</h2>
      <router-link to="/user/my-trainings" class="text-sm text-teal-600 hover:underline">
        Все →
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500">
      Загрузка...
    </div>

    <div v-else-if="trainings.length === 0" class="text-gray-500 text-center py-8">
      Вы ещё не записаны ни на одну тренировку
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="training in upcomingTrainings"
        :key="training.id"
        class="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
      >
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <span class="font-medium text-gray-900">
              {{ formatDate(training.training_date) }}
            </span>
            <span
              class="px-2 py-0.5 rounded text-xs font-medium"
              :class="training.status === 'registered' ? 'bg-teal-100 text-teal-700' : 'bg-yellow-100 text-yellow-700'"
            >
              {{ training.status === 'registered' ? 'Записан' : 'Резерв' }}
            </span>
          </div>
          <p class="text-sm text-gray-500">⏰ {{ training.training_time }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const trainings = ref([])
const loading = ref(false)

onMounted(() => {
  loadMyTrainings()
})

const loadMyTrainings = async () => {
  loading.value = true

  try {
    const response = await fetch('/api/user/my-trainings', {
      credentials: 'include'
    })

    if (!response.ok) {
      throw new Error('Failed to load trainings')
    }

    const data = await response.json()
    trainings.value = data.trainings || []
  } catch (error) {
    console.error('Error loading trainings:', error)
  } finally {
    loading.value = false
  }
}

const upcomingTrainings = computed(() => {
  // Показываем первые 3 тренировки
  return trainings.value.slice(0, 3)
})

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  const day = date.getDate()
  const month = date.toLocaleDateString('ru-RU', { month: 'short' })
  const weekday = date.toLocaleDateString('ru-RU', { weekday: 'short' })
  return `${weekday}, ${day} ${month}`
}
</script>
