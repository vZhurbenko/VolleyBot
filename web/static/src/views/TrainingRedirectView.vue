<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
    <div class="bg-white rounded shadow p-6 lg:p-10 w-full max-w-md text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mx-auto mb-4"></div>
      <p class="text-gray-600">Переход к тренировке...</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

onMounted(async () => {
  const trainingUuid = route.params.uuid
  
  try {
    const response = await fetch(`/training/${trainingUuid}`, {
      credentials: 'include',
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.redirect) {
        // Используем window.location для полного редиректа
        window.location.href = data.redirect
      }
    } else if (response.status === 404) {
      // Тренировка не найдена
      window.location.href = '/dashboard/calendar'
    }
  } catch (error) {
    console.error('Ошибка редиректа:', error)
    window.location.href = '/dashboard/calendar'
  }
})
</script>
