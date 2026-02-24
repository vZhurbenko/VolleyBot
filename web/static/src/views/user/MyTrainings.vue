<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Мои тренировки</h1>

    <div v-if="loading" class="text-center py-8 text-gray-500">
      Загрузка...
    </div>

    <div v-else-if="trainings.length === 0" class="text-center py-8 text-gray-500">
      Вы ещё не записаны ни на одну тренировку
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="training in trainings"
        :key="training.id"
        class="flex items-center justify-between p-4 bg-gray-50 rounded"
      >
        <div class="flex-1">
          <!-- Название тренировки -->
          <p v-if="training.training_name || training.schedule_name" class="text-base font-semibold text-gray-900 mb-1">
            {{ training.training_name || training.schedule_name }}
          </p>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-lg font-semibold text-gray-900">
              {{ formatDate(training.training_date) }}
            </span>
            <span
              class="px-2 py-0.5 rounded text-xs font-medium"
              :class="training.status === 'registered' ? 'bg-teal-100 text-teal-700' : 'bg-yellow-100 text-yellow-700'"
            >
              {{ training.status === 'registered' ? 'Записан' : 'Резерв' }}
            </span>
          </div>
          <p class="text-sm text-gray-500">
            ⏰ {{ training.training_time }}
          </p>
        </div>

        <button
          @click="unregister(training)"
          class="px-4 py-2 rounded font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent"
        >
          Выписаться
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

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

const unregister = async (training) => {
  if (!confirm('Выписаться с тренировки?')) return
  
  try {
    const response = await fetch('/api/user/calendar/unregister', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        training_date: training.training_date,
        training_time: training.training_time,
        chat_id: training.chat_id
      })
    })
    
    const result = await response.json()
    
    if (response.ok && result.success) {
      loadMyTrainings()
    } else {
      alert(result.detail || 'Ошибка отписки')
    }
  } catch (error) {
    console.error('Error unregistering:', error)
    alert('Ошибка отписки от тренировки')
  }
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
  return date.toLocaleDateString('ru-RU', options)
}
</script>
