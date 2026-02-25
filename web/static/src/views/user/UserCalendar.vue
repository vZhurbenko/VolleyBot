<template>
  <div class="flex flex-col gap-6">
    <!-- Заголовок для мобильных -->
    <div class="lg:hidden">
      <h1 class="text-2xl font-bold text-gray-900">Календарь тренировок</h1>
    </div>

    <!-- Календарь -->
    <Calendar
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
import Calendar from '@/components/Calendar.vue'
import TrainingModal from '@/components/TrainingModal.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { useConfirmStore } from '@/stores/confirm'

const route = useRoute()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const confirmStore = useConfirmStore()

const trainings = ref([])
const selectedTraining = ref(null)
const loading = ref(false)

// Получаем календарь при загрузке
onMounted(() => {
  loadCalendar()
})

// Следим за изменением query параметров (месяц/год)
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
  loadCalendar() // Обновляем данные после закрытия
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
      selectedTraining.value.registered_count = result.status === 'registered'
        ? selectedTraining.value.registered_count + 1
        : selectedTraining.value.registered_count
      loadCalendar()
    } else {
      notificationsStore.error(result.detail || 'Ошибка записи')
    }
  } catch (error) {
    console.error('Error registering:', error)
    notificationsStore.error('Ошибка записи на тренировку')
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
      selectedTraining.value.registered_count = Math.max(0, selectedTraining.value.registered_count - 1)
      loadCalendar()
    } else {
      notificationsStore.error(result.detail || 'Ошибка отписки')
    }
  } catch (error) {
    console.error('Error unregistering:', error)
    notificationsStore.error('Ошибка отписки от тренировки')
  }
}

const removeOneTimeTraining = async () => {
  if (!selectedTraining.value || !authStore.isAdmin) return

  const confirmed = await confirmStore.danger('Удалить эту тренировку?')
  if (!confirmed) return

  try {
    const response = await fetch(`/api/admin/calendar/remove-training/${selectedTraining.value.date}_${selectedTraining.value.time}_${selectedTraining.value.chat_id}`, {
      method: 'DELETE',
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      closeTrainingModal()
      notificationsStore.success('Тренировка удалена')
    } else {
      notificationsStore.error(result.detail || 'Ошибка удаления')
    }
  } catch (error) {
    console.error('Error removing training:', error)
    notificationsStore.error('Ошибка удаления тренировки')
  }
}
</script>
