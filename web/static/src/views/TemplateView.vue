<template>
  <div class="flex flex-col gap-4">
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
import { useNotificationsStore } from '@/stores/notifications'
import TemplateForm from '@/components/TemplateForm.vue'

const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()

onMounted(async () => {
  await settingsStore.loadTemplate()
})

const handleSave = async (templateData) => {
  const success = await settingsStore.saveTemplate(templateData)
  if (!success) {
    notificationsStore.error('Ошибка сохранения')
  } else {
    notificationsStore.success('Шаблон сохранён')
  }
}
</script>
