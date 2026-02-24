<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Записи на тренировки</h1>

    <!-- Фильтр по дате -->
    <div class="flex flex-wrap gap-4 mb-6">
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium text-gray-700">С даты</label>
        <input
          v-model="startDate"
          type="date"
          class="h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
          @change="loadTrainings"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-sm font-medium text-gray-700">По дату</label>
        <input
          v-model="endDate"
          type="date"
          class="h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
          @change="loadTrainings"
        />
      </div>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500">
      Загрузка...
    </div>

    <div v-else-if="trainings.length === 0" class="text-center py-8 text-gray-500">
      Нет записей за выбранный период
    </div>

    <div v-else class="space-y-6">
      <!-- Группировка по датам -->
      <div
        v-for="(group, date) in groupedTrainings"
        :key="date"
        class="border border-gray-200 rounded-lg overflow-hidden"
      >
        <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 class="font-semibold text-gray-900">{{ formatDate(date) }}</h3>
        </div>
        <div class="divide-y divide-gray-100">
          <div
            v-for="training in group"
            :key="training.id"
            class="px-4 py-3 flex items-center justify-between"
          >
            <div>
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-900">{{ training.time }}</span>
                <span
                  class="px-2 py-0.5 rounded text-xs font-medium"
                  :class="training.status === 'registered' ? 'bg-teal-100 text-teal-700' : 'bg-yellow-100 text-yellow-700'"
                >
                  {{ training.status === 'registered' ? 'Записан' : 'Резерв' }}
                </span>
              </div>
              <p class="text-sm text-gray-500">
                {{ training.first_name }} {{ training.last_name || '' }}
                <span v-if="training.username" class="text-gray-400">@{{ training.username }}</span>
              </p>
            </div>
            <!-- Кнопка удаления для админа -->
            <button
              @click="removeUser(training)"
              class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors"
              title="Удалить участника"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const startDate = ref('')
const endDate = ref('')
const trainings = ref([])
const loading = ref(false)

onMounted(() => {
  // Устанавливаем даты по умолчанию (текущий месяц)
  const now = new Date()
  startDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
  endDate.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
  
  loadTrainings()
})

const loadTrainings = async () => {
  loading.value = true
  
  try {
    const response = await fetch(`/api/admin/trainings?start_date=${startDate.value}&end_date=${endDate.value}`, {
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

const groupedTrainings = computed(() => {
  const groups = {}
  
  trainings.value.forEach(t => {
    const key = `${t.training_date}_${t.chat_id || ''}`
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push({
      ...t,
      time: t.training_time
    })
  })
  
  // Сортируем даты
  const sorted = {}
  Object.keys(groups).sort().forEach(key => {
    sorted[key] = groups[key]
  })
  
  return sorted
})

const formatDate = (dateKey) => {
  const [date, chatId] = dateKey.split('_')
  const d = new Date(date)
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
  return d.toLocaleDateString('ru-RU', options)
}

const removeUser = async (training) => {
  const name = training.first_name + (training.last_name ? ' ' + training.last_name : '')
  if (!confirm(`Удалить ${name} из тренировки ${training.training_date}?`)) return

  try {
    const response = await fetch(
      `/api/admin/calendar/remove-user/${training.training_date}/${encodeURIComponent(training.training_time)}/${training.chat_id}/${training.user_telegram_id}`,
      {
        method: 'DELETE',
        credentials: 'include'
      }
    )

    const result = await response.json()

    if (response.ok && result.success) {
      // Перезагружаем список
      await loadTrainings()
    } else {
      alert(result.detail || 'Ошибка удаления участника')
    }
  } catch (error) {
    console.error('Error removing user:', error)
    alert('Ошибка удаления участника')
  }
}
</script>
