<template>
  <div class="space-y-6">
    <div class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">Название</label>
      <input
        v-model="form.name"
        type="text"
        class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        placeholder="Название шаблона"
      />
    </div>

    <div class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">Описание</label>
      <textarea
        v-model="form.description"
        rows="3"
        class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        placeholder="Описание тренировки"
      ></textarea>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">День тренировки</label>
        <select
          v-model="form.training_day"
          class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        >
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
        <label class="block text-sm font-medium text-gray-700">День опроса</label>
        <select
          v-model="form.poll_day"
          class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
        >
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
        <label class="block text-sm font-medium text-gray-700">Время</label>
        <input
          v-model="form.training_time"
          type="text"
          class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="18:00 - 20:00"
        />
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-gray-200">
      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Chat ID по умолчанию</label>
        <input
          v-model="form.default_chat_id"
          type="text"
          class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="-1002588984009"
        />
      </div>

      <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700">Topic ID по умолчанию (опционально)</label>
        <input
          v-model.number="form.default_topic_id"
          type="number"
          class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
          placeholder="Оставьте пустым если не используется"
        />
      </div>
    </div>

    <div class="pt-6 border-t border-gray-200">
      <button @click="handleSave" class="px-6 py-3 rounded-lg font-medium transition-colors bg-gray-900 text-white hover:bg-gray-800">
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
  enabled: true,
  default_chat_id: '',
  default_topic_id: null
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
      enabled: newTemplate.enabled !== false,
      default_chat_id: newTemplate.default_chat_id || '',
      default_topic_id: newTemplate.default_topic_id !== undefined ? newTemplate.default_topic_id : null
    }
  }
}, { immediate: true })

const handleSave = () => {
  emit('save', { ...form.value })
}
</script>
