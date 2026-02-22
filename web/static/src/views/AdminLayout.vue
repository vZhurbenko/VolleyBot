<template>
  <div class="flex min-h-screen bg-gray-50">
    <Sidebar />
    
    <div class="flex-1 flex flex-col">
      <Topbar>
        <template #title>{{ pageTitle }}</template>
      </Topbar>
      
      <main class="flex-1 p-6 overflow-auto">
        <div class="max-w-7xl mx-auto">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import Topbar from '@/components/Topbar.vue'

const route = useRoute()

const pageTitle = computed(() => {
  const titles = {
    dashboard: 'Панель управления',
    template: 'Шаблон опроса',
    schedules: 'Расписания',
    polls: 'Опросы',
    admins: 'Администраторы'
  }
  return titles[route.name] || 'VolleyBot Admin'
})
</script>
