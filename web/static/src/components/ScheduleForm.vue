<template>
  <form @submit.prevent="handleSubmit" class="flex flex-col gap-4 lg:gap-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">Название</label>
        <input
          v-model="form.name"
          type="text"
          class="w-full h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors"
          placeholder="Например: Воскресенье"
          required
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">Chat ID</label>
        <input
          v-model="form.chat_id"
          type="text"
          class="w-full h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors"
          placeholder="-1002588984009"
          required
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">Topic ID (опционально)</label>
        <input
          v-model.number="form.message_thread_id"
          type="number"
          class="w-full h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors"
          placeholder="Оставьте пустым если не используется"
        />
      </div>

      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">День тренировки</label>
        <select v-model="form.training_day" class="w-full h-11 px-4 border border-gray-300 rounded appearance-none bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors">
          <option value="monday">Понедельник</option>
          <option value="tuesday">Вторник</option>
          <option value="wednesday">Среда</option>
          <option value="thursday">Четверг</option>
          <option value="friday">Пятница</option>
          <option value="saturday">Суббота</option>
          <option value="sunday">Воскресенье</option>
        </select>
      </div>

      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">День создания опроса</label>
        <select v-model="form.poll_day" class="w-full h-11 px-4 border border-gray-300 rounded appearance-none bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors">
          <option value="monday">Понедельник</option>
          <option value="tuesday">Вторник</option>
          <option value="wednesday">Среда</option>
          <option value="thursday">Четверг</option>
          <option value="friday">Пятница</option>
          <option value="saturday">Суббота</option>
          <option value="sunday">Воскресенье</option>
        </select>
      </div>

      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">Время тренировки</label>
        <input
          v-model="form.training_time"
          type="text"
          class="w-full h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors"
          placeholder="18:00 - 20:00"
        />
      </div>
    </div>

    <div class="pt-4 border-t border-gray-200">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-700">Включено</p>
          <p class="text-xs text-gray-500">Активное расписание</p>
        </div>
        <Toggle
          :model-value="form.enabled"
          @toggle="form.enabled = !form.enabled"
        />
      </div>
    </div>

    <div class="flex flex-wrap gap-3 pt-6 border-t border-gray-200">
      <button type="submit" class="h-11 px-6 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700">
        {{ isEdit ? 'Сохранить' : 'Добавить' }}
      </button>
      <button type="button" @click.stop="$emit('cancel')" class="h-11 px-6 rounded font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200">
        Отмена
      </button>
    </div>
  </form>
</template>

<script setup>
import { ref, watch } from 'vue'
import Toggle from '@/components/Toggle.vue'

const props = defineProps({
  schedule: {
    type: Object,
    default: null
  },
  isEdit: {
    type: Boolean,
    default: false
  },
  defaultChatId: {
    type: String,
    default: ''
  },
  defaultTopicId: {
    type: [Number, String],
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const defaultForm = {
  name: '',
  chat_id: props.defaultChatId || '',
  message_thread_id: props.defaultTopicId || null,
  training_day: 'sunday',
  poll_day: 'friday',
  training_time: '18:00 - 20:00',
  enabled: true
}

const form = ref({ ...defaultForm })

watch(() => props.schedule, (newSchedule) => {
  if (newSchedule) {
    form.value = {
      name: newSchedule.name || '',
      chat_id: newSchedule.chat_id || '',
      message_thread_id: newSchedule.message_thread_id || null,
      training_day: newSchedule.training_day || 'sunday',
      poll_day: newSchedule.poll_day || 'friday',
      training_time: newSchedule.training_time || '18:00 - 20:00',
      enabled: newSchedule.enabled !== false
    }
  } else if (!props.isEdit) {
    // Сброс к значениям по умолчанию при открытии формы добавления
    form.value = {
      name: '',
      chat_id: props.defaultChatId || '',
      message_thread_id: props.defaultTopicId || null,
      training_day: 'sunday',
      poll_day: 'friday',
      training_time: '18:00 - 20:00',
      enabled: true
    }
  }
}, { immediate: true })

watch(() => props.defaultChatId, (newVal) => {
  if (!props.isEdit && !form.value.chat_id) {
    form.value.chat_id = newVal
  }
})

watch(() => props.defaultTopicId, (newVal) => {
  if (!props.isEdit && !form.value.message_thread_id) {
    form.value.message_thread_id = newVal
  }
})

const handleSubmit = () => {
  emit('submit', { ...form.value })
}
</script>
