<template>
  <div class="space-y-4">
    <div v-if="settingsStore.template">
      <TemplateForm 
        :template="settingsStore.template" 
        @save="handleSave" 
      />
    </div>
    <div v-else class="text-gray-500 text-center py-8">
      Загрузка...
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import TemplateForm from '@/components/TemplateForm.vue'

const settingsStore = useSettingsStore()

onMounted(async () => {
  await settingsStore.loadTemplate()
})

const handleSave = async (templateData) => {
  const success = await settingsStore.saveTemplate(templateData)
  if (success) {
    alert('Шаблон сохранён!')
  } else {
    alert('Ошибка сохранения')
  }
}
</script>
