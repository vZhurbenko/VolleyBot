<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <div class="flex justify-end mb-4">
      <button @click="showForm = true" class="h-11 px-6 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700 whitespace-nowrap">
        + Добавить расписание
      </button>
    </div>

    <div v-if="settingsStore.schedules.length > 0" class="divide-y divide-gray-100">
      <ScheduleItem
        v-for="schedule in settingsStore.schedules"
        :key="schedule.id"
        :schedule="schedule"
        @edit="handleEdit"
        @delete="handleDelete"
      />
    </div>
    <div v-else class="text-gray-500 text-center py-8">
      Нет расписаний
    </div>

    <!-- Модальное окно -->
    <div v-if="showForm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click="closeModal">
      <div class="bg-white rounded shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto" @click.stop>
        <div class="px-4 lg:px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white">
          <h2 class="text-lg font-semibold">{{ editingSchedule ? 'Редактировать расписание' : 'Новое расписание' }}</h2>
          <button @click="closeModal" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100 transition-colors">✕</button>
        </div>

        <div class="p-4 lg:p-6">
          <ScheduleForm
            :schedule="editingSchedule"
            :is-edit="!!editingSchedule"
            :default-chat-id="defaultChatId"
            :default-topic-id="defaultTopicId"
            @submit="handleSubmit"
            @cancel="closeModal"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import ScheduleItem from '@/components/ScheduleItem.vue'
import ScheduleForm from '@/components/ScheduleForm.vue'

const settingsStore = useSettingsStore()

const showForm = ref(false)
const editingSchedule = ref(null)
const defaultChatId = ref('')
const defaultTopicId = ref(null)

onMounted(async () => {
  await Promise.all([
    settingsStore.loadSchedules(),
    settingsStore.loadTemplate()
  ])
  
  // Загружаем значения по умолчанию из шаблона
  const template = settingsStore.template
  if (template) {
    defaultChatId.value = template.default_chat_id || ''
    defaultTopicId.value = template.default_topic_id !== undefined ? template.default_topic_id : null
  }
})

const handleEdit = (schedule) => {
  editingSchedule.value = schedule
  showForm.value = true
}

const handleDelete = async (id) => {
  if (!confirm('Удалить это расписание?')) return
  const success = await settingsStore.deleteSchedule(id)
  if (!success) {
    alert('Ошибка удаления')
  }
}

const handleSubmit = async (scheduleData) => {
  let success
  if (editingSchedule.value) {
    success = await settingsStore.updateSchedule(editingSchedule.value.id, scheduleData)
  } else {
    success = await settingsStore.addSchedule(scheduleData)
  }

  if (success) {
    closeModal()
  } else {
    alert('Ошибка сохранения')
  }
}

const closeModal = () => {
  showForm.value = false
  editingSchedule.value = null
}
</script>
