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
  // === НАЧАЛО onMounted ===
  console.log('=== TrainingRedirectView mounted ===')
  console.log('[TrainingRedirect] Начало onMounted')
  
  const trainingUuid = route.params.uuid
  
  // === Логирование параметров route ===
  console.log('[TrainingRedirect] Середина onMounted - параметры route:')
  console.log('[TrainingRedirect] - uuid:', trainingUuid)
  console.log('[TrainingRedirect] - all params:', route.params)
  console.log('[TrainingRedirect] - path:', route.path)
  console.log('[TrainingRedirect] - fullPath:', route.fullPath)
  console.log('[TrainingRedirect] - query:', route.query)
  
  // Конец логирования параметров
  console.log('[TrainingRedirect] Конец логирования параметров route')

  if (!trainingUuid) {
    console.error('[TrainingRedirect] UUID не найден в параметрах!')
    console.log('[TrainingRedirect] Редирект на /dashboard/calendar (нет UUID)')
    window.location.href = '/dashboard/calendar'
    return
  }

  try {
    // Запрашиваем бэкенд endpoint /training/{uuid} для получения редиректа
    console.log('[TrainingRedirect] Fetching /training/' + trainingUuid)

    const response = await fetch(`/training/${trainingUuid}`, {
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
      },
    })

    // === Логирование ответа от fetch ===
    console.log('[TrainingRedirect] Ответ от fetch:')
    console.log('[TrainingRedirect] - status:', response.status)
    console.log('[TrainingRedirect] - ok:', response.ok)
    console.log('[TrainingRedirect] - statusText:', response.statusText)
    console.log('[TrainingRedirect] - headers:', response.headers)
    
    const data = await response.json()
    console.log('[TrainingRedirect] Response data:', data)
    console.log('[TrainingRedirect] - data.redirect:', data.redirect)
    // Конец логирования ответа
    console.log('[TrainingRedirect] Конец логирования ответа от fetch')

    if (data.redirect) {
      const redirectUrl = data.redirect
      console.log('[TrainingRedirect] Redirect найден:', redirectUrl)
      console.log('[TrainingRedirect] Момент перед window.location.href')
      console.log('=== Setting href to:', redirectUrl)
      
      // Пробуем разные способы редиректа
      setTimeout(() => {
        console.log('[TrainingRedirect] Выполнение редиректа в setTimeout')
        window.location.href = redirectUrl
      }, 100)
      return
    }

    // Если нет redirect, идём в календарь
    console.log('[TrainingRedirect] No redirect в data, редирект на /dashboard/calendar')
    window.location.href = '/dashboard/calendar'
  } catch (error) {
    console.error('[TrainingRedirect] Ошибка редиректа:', error)
    console.error('[TrainingRedirect] Error name:', error.name)
    console.error('[TrainingRedirect] Error message:', error.message)
    console.error('[TrainingRedirect] Error stack:', error.stack)
    console.log('[TrainingRedirect] Редирект на /dashboard/calendar (error)')
    window.location.href = '/dashboard/calendar'
  }
  
  // === КОНЕЦ onMounted ===
  console.log('[TrainingRedirect] Конец onMounted')
})
</script>
