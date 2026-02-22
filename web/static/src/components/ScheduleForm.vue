<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Название</label>
        <input 
          v-model="form.name" 
          type="text" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="Например: Воскресенье"
          required
        />
      </div>
      
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Chat ID</label>
        <input 
          v-model="form.chat_id" 
          type="text" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="-1002588984009"
          required
        />
      </div>
      
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Topic ID (опционально)</label>
        <input 
          v-model.number="form.message_thread_id" 
          type="number" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="Оставьте пустым если не используется"
        />
      </div>
      
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">День тренировки</label>
        <select v-model="form.training_day" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors">
          <option value="monday">Понедельник</option>
          <option value="tuesday">Вторник</option>
          <option value="wednesday">Среда</option>
          <option value="thursday">Четверг</option>
          <option value="friday">Пятница</option>
          <option value="saturday">Суббота</option>
          <option value="sunday">Воскресенье</option>
        </select>
      </div>
      
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">День создания опроса</label>
        <select v-model="form.poll_day" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors">
          <option value="monday">Понедельник</option>
          <option value="tuesday">Вторник</option>
          <option value="wednesday">Среда</option>
          <option value="thursday">Четверг</option>
          <option value="friday">Пятница</option>
          <option value="saturday">Суббота</option>
          <option value="sunday">Воскресенье</option>
        </select>
      </div>
      
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Время тренировки</label>
        <input 
          v-model="form.training_time" 
          type="text" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="18:00 - 20:00"
        />
      </div>
    </div>
    
    <div class="pt-2">
      <label class="flex items-center gap-2 cursor-pointer">
        <input v-model="form.enabled" type="checkbox" class="w-4 h-4 text-blue-600 rounded focus:ring-blue-500" />
        <span class="text-sm text-gray-700">Включено</span>
      </label>
    </div>
    
    <div class="flex gap-2 pt-4 border-t border-gray-100">
      <button type="submit" class="px-4 py-2 rounded-lg font-medium transition-colors bg-gray-900 text-white hover:bg-gray-800">
        {{ isEdit ? 'Сохранить' : 'Добавить' }}
      </button>
      <button type="button" @click="$emit('cancel')" class="px-4 py-2 rounded-lg font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200">
        Отмена
      </button>
    </div>
  </form>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  schedule: {
    type: Object,
    default: null
  },
  isEdit: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit', 'cancel'])

const defaultForm = {
  name: '',
  chat_id: '',
  message_thread_id: null,
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
  } else {
    form.value = { ...defaultForm }
  }
}, { immediate: true })

const handleSubmit = () => {
  emit('submit', { ...form.value })
}
</script>
