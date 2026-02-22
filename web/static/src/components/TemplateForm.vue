<template>
  <div class="space-y-4">
    <div class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">Название</label>
      <input 
        v-model="form.name" 
        type="text" 
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        placeholder="Название шаблона"
      />
    </div>
    
    <div class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">Описание</label>
      <textarea 
        v-model="form.description" 
        rows="2"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        placeholder="Описание тренировки"
      ></textarea>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">День тренировки</label>
        <input 
          v-model="form.training_day" 
          type="text" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="Например: Воскресенье"
        />
      </div>
      
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">День опроса</label>
        <input 
          v-model="form.poll_day" 
          type="text" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="Например: Пятница"
        />
      </div>
      
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Время</label>
        <input 
          v-model="form.training_time" 
          type="text" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="18:00 - 20:00"
        />
      </div>
    </div>
    
    <div class="pt-4">
      <button @click="handleSave" class="px-4 py-2 rounded-lg font-medium transition-colors bg-gray-900 text-white hover:bg-gray-800">
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
