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
  
  console.log('TrainingRedirect: UUID =', trainingUuid)
  
  try {
    // Запрашиваем бэкенд endpoint /training/{uuid} для получения редиректа
    const response = await fetch(`/training/${trainingUuid}`, {
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
      },
    })
    
    console.log('TrainingRedirect: response status =', response.status)
    
    const data = await response.json()
    console.log('TrainingRedirect: response data =', data)
    
    if (data.redirect) {
      console.log('TrainingRedirect: redirecting to', data.redirect)
      // Используем window.location для полного редиректа
      window.location.replace(data.redirect)
      return
    }
    
    // Если нет redirect, идём в календарь
    window.location.href = '/dashboard/calendar'
  } catch (error) {
    console.error('TrainingRedirect: ошибка редиректа:', error)
    window.location.href = '/dashboard/calendar'
  }
})
</script>
