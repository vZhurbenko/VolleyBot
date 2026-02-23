<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Календарь тренировок</h1>

    <div v-if="loading" class="text-center py-8 text-gray-500">
      Загрузка...
    </div>

    <Calendar
      v-else
      :trainings="trainings"
      @click-training="openTrainingModal"
    />

    <!-- Модалка тренировки -->
    <TrainingModal
      v-if="selectedTraining"
      :training="selectedTraining"
      @close="closeTrainingModal"
      @register="registerForTraining"
      @unregister="unregisterFromTraining"
      @remove-training="removeOneTimeTraining"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Calendar from '@/components/Calendar.vue'
import TrainingModal from '@/components/TrainingModal.vue'

const route = useRoute()
const authStore = useAuthStore()

const trainings = ref([])
const selectedTraining = ref(null)
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

const openTrainingModal = (training) => {
  selectedTraining.value = { ...training }
}

const closeTrainingModal = () => {
  selectedTraining.value = null
  loadCalendar()
}

const registerForTraining = async () => {
  if (!selectedTraining.value) return

  try {
    const response = await fetch('/api/user/calendar/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        training_date: selectedTraining.value.date,
        training_time: selectedTraining.value.time,
        chat_id: selectedTraining.value.chat_id,
        topic_id: selectedTraining.value.topic_id
      })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      selectedTraining.value.user_status = result.status
      loadCalendar()
    } else {
      alert(result.detail || 'Ошибка записи')
    }
  } catch (error) {
    console.error('Error registering:', error)
    alert('Ошибка записи на тренировку')
  }
}

const unregisterFromTraining = async () => {
  if (!selectedTraining.value) return

  try {
    const response = await fetch('/api/user/calendar/unregister', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        training_date: selectedTraining.value.date,
        training_time: selectedTraining.value.time,
        chat_id: selectedTraining.value.chat_id
      })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      selectedTraining.value.user_status = null
      loadCalendar()
    } else {
      alert(result.detail || 'Ошибка отписки')
    }
  } catch (error) {
    console.error('Error unregistering:', error)
    alert('Ошибка отписки от тренировки')
  }
}

const removeOneTimeTraining = async () => {
  if (!selectedTraining.value || !authStore.isAdmin) return

  if (!confirm('Удалить эту тренировку?')) return

  try {
    const response = await fetch(`/api/admin/calendar/remove-training/${selectedTraining.value.date}_${selectedTraining.value.time}_${selectedTraining.value.chat_id}`, {
      method: 'DELETE',
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      closeTrainingModal()
      alert('Тренировка удалена')
    } else {
      alert(result.detail || 'Ошибка удаления')
    }
  } catch (error) {
    console.error('Error removing training:', error)
    alert('Ошибка удаления тренировки')
  }
}
</script>
