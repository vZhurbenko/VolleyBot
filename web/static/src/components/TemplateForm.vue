<template>
  <div class="template-form">
    <div class="form-group">
      <label class="form-label">Название</label>
      <input 
        v-model="form.name" 
        type="text" 
        class="form-input"
        placeholder="Название шаблона"
      />
    </div>
    
    <div class="form-group">
      <label class="form-label">Описание</label>
      <textarea 
        v-model="form.description" 
        rows="2"
        class="form-input"
        placeholder="Описание тренировки"
      ></textarea>
    </div>
    
    <div class="form-grid">
      <div class="form-group">
        <label class="form-label">День тренировки</label>
        <input 
          v-model="form.training_day" 
          type="text" 
          class="form-input"
          placeholder="Например: Воскресенье"
        />
      </div>
      
      <div class="form-group">
        <label class="form-label">День опроса</label>
        <input 
          v-model="form.poll_day" 
          type="text" 
          class="form-input"
          placeholder="Например: Пятница"
        />
      </div>
      
      <div class="form-group">
        <label class="form-label">Время</label>
        <input 
          v-model="form.training_time" 
          type="text" 
          class="form-input"
          placeholder="18:00 - 20:00"
        />
      </div>
    </div>
    
    <div class="form-actions">
      <button @click="handleSave" class="btn btn-primary">
        Сохранить
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  template: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['save'])

const defaultForm = {
  name: '',
  description: '',
  training_day: '',
  poll_day: '',
  training_time: '',
  options: ['Буду', '50/50', 'Не буду'],
  enabled: true
}

const form = ref({ ...defaultForm })

watch(() => props.template, (newTemplate) => {
  if (newTemplate) {
    form.value = {
      name: newTemplate.name || '',
      description: newTemplate.description || '',
      training_day: newTemplate.training_day || '',
      poll_day: newTemplate.poll_day || '',
      training_time: newTemplate.training_time || '',
      options: newTemplate.options || ['Буду', '50/50', 'Не буду'],
      enabled: newTemplate.enabled !== false
    }
  }
}, { immediate: true })

const handleSave = () => {
  emit('save', { ...form.value })
}
</script>

<style scoped>
.template-form {
  @apply space-y-4;
}

.form-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
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

.form-actions {
  @apply pt-4;
}

.btn {
  @apply px-4 py-2 rounded-lg font-medium transition-colors;
}

.btn-primary {
  @apply bg-gray-900 text-white hover:bg-gray-800;
}
</style>
