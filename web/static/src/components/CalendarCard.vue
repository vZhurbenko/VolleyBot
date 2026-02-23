<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-900">Календарь тренировок</h2>
      <router-link to="/user/calendar" class="text-sm text-teal-600 hover:underline">
        Открыть →
      </router-link>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500">
      Загрузка...
    </div>

    <div v-else-if="trainings.length === 0" class="text-gray-500 text-center py-8">
      Нет тренировок в этом месяце
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="training in upcomingTrainings"
        :key="`${training.date}_${training.time}_${training.chat_id}`"
        class="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded bg-teal-100 flex items-center justify-center text-lg font-bold text-teal-700">
            {{ getDayNumber(training.date) }}
          </div>
          <div>
            <p class="font-medium text-gray-900">{{ getDayName(training.date) }}</p>
            <p class="text-sm text-gray-500">{{ training.time }}</p>
          </div>
        </div>
        <div class="text-right">
          <p class="text-sm font-medium text-gray-900">
            {{ training.registered_count }}/{{ training.registered_count + training.waitlist_count + (12 - training.registered_count - training.waitlist_count) }}
          </p>
          <p class="text-xs text-gray-500">записано</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const trainings = ref([])
const loading = ref(false)

onMounted(() => {
  loadCalendar()
})

watch(() => route.query, () => {
  loadCalendar()
})

const loadCalendar = async () => {
  loading.value = true

  const now = new Date()
  const year = route.query.year || now.getFullYear()
  const month = route.query.month || now.getMonth() + 1

  try {
    const response = await fetch(`/api/user/calendar?year=${year}&month=${month}`)

    if (!response.ok) {
      throw new Error('Failed to load calendar')
    }

    const data = await response.json()
    trainings.value = data.trainings || []
  } catch (error) {
    console.error('Error loading calendar:', error)
  } finally {
    loading.value = false
  }
}

const upcomingTrainings = computed(() => {
  // Показываем первые 3 тренировки
  return trainings.value.slice(0, 3)
})

const dayNames = {
  0: 'Вс', 1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб'
}

const getDayName = (dateStr) => {
  const date = new Date(dateStr)
  const dayName = dayNames[date.getDay()]
  const day = date.getDate()
  const month = date.toLocaleDateString('ru-RU', { month: 'short' })
  return `${dayName}, ${day} ${month}`
}

const getDayNumber = (dateStr) => {
  const date = new Date(dateStr)
  return date.getDate()
}
</script>
