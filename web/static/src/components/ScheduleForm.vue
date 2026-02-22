<template>
  <form @submit.prevent="handleSubmit" class="schedule-form">
    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">Название</label>
        <input 
          v-model="form.name" 
          type="text" 
          class="form-input"
          placeholder="Например: Воскресенье"
          required
        />
      </div>
      
      <div class="form-group">
        <label class="form-label">Chat ID</label>
        <input 
          v-model="form.chat_id" 
          type="text" 
          class="form-input"
          placeholder="-1002588984009"
          required
        />
      </div>
      
      <div class="form-group">
        <label class="form-label">Topic ID (опционально)</label>
        <input 
          v-model.number="form.message_thread_id" 
          type="number" 
          class="form-input"
          placeholder="Оставьте пустым если не используется"
        />
      </div>
      
      <div class="form-group">
        <label class="form-label">День тренировки</label>
        <select v-model="form.training_day" class="form-input">
          <option value="monday">Понедельник</option>
          <option value="tuesday">Вторник</option>
          <option value="wednesday">Среда</option>
          <option value="thursday">Четверг</option>
          <option value="friday">Пятница</option>
          <option value="saturday">Суббота</option>
          <option value="sunday">Воскресенье</option>
        </select>
      </div>
      
      <div class="form-group">
        <label class="form-label">День создания опроса</label>
        <select v-model="form.poll_day" class="form-input">
          <option value="monday">Понедельник</option>
          <option value="tuesday">Вторник</option>
          <option value="wednesday">Среда</option>
          <option value="thursday">Четверг</option>
          <option value="friday">Пятница</option>
          <option value="saturday">Суббота</option>
          <option value="sunday">Воскресенье</option>
        </select>
      </div>
      
      <div class="form-group">
        <label class="form-label">Время тренировки</label>
        <input 
          v-model="form.training_time" 
          type="text" 
          class="form-input"
          placeholder="18:00 - 20:00"
        />
      </div>
    </div>
    
    <div class="form-group checkbox-group">
      <label class="checkbox-label">
        <input v-model="form.enabled" type="checkbox" class="checkbox" />
        <span>Включено</span>
      </label>
    </div>
    
    <div class="form-actions">
      <button type="submit" class="btn btn-primary">
        {{ isEdit ? 'Сохранить' : 'Добавить' }}
      </button>
      <button type="button" @click="$emit('cancel')" class="btn btn-secondary">
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

<style scoped>
.schedule-form {
  @apply space-y-4;
}

.form-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4;
}

.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-medium text-gray-700;
}

.form-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors;
}

.checkbox-group {
  @apply pt-2;
}

.checkbox-label {
  @apply flex items-center gap-2 cursor-pointer;
}

.checkbox {
  @apply w-4 h-4 text-blue-600 rounded focus:ring-blue-500;
}

.form-actions {
  @apply flex gap-2 pt-4 border-t border-gray-100;
}

.btn {
  @apply px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-gray-900 text-white hover:bg-gray-800;
}

.btn-secondary {
  @apply bg-gray-100 text-gray-700 hover:bg-gray-200;
}
</style>
