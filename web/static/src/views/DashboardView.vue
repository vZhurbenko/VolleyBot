<template>
  <div class="flex min-h-screen bg-gray-50">
    <Sidebar />
    
    <div class="flex-1 flex flex-col">
      <Topbar>
        <template #title>Панель управления</template>
      </Topbar>
      
      <main class="flex-1 p-6 overflow-auto">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-7xl">
          <!-- Шаблон опроса -->
          <DashboardCard icon="📋">
            <template #title>Шаблон опроса</template>
            
            <template v-if="settingsStore.template">
              <TemplateForm 
                :template="settingsStore.template" 
                @save="handleSaveTemplate" 
              />
            </template>
            <template v-else>
              <div class="text-gray-500 text-center py-8">Загрузка...</div>
            </template>
          </DashboardCard>
          
          <!-- Расписания -->
          <DashboardCard icon="📅">
            <template #title>Расписания опросов</template>
            <template #header-action>
              <button @click="showAddSchedule = true" class="px-3 py-1.5 rounded-lg font-medium transition-colors text-sm bg-gray-900 text-white hover:bg-gray-800">
                + Добавить
              </button>
            </template>
            
            <div v-if="settingsStore.schedules.length > 0" class="divide-y divide-gray-100">
              <ScheduleItem
                v-for="schedule in settingsStore.schedules"
                :key="schedule.id"
                :schedule="schedule"
                @edit="handleEditSchedule"
                @delete="handleDeleteSchedule"
              />
            </div>
            <div v-else class="text-gray-500 text-center py-8">
              Нет расписаний
            </div>
          </DashboardCard>
          
          <!-- Активные опросы -->
          <DashboardCard icon="📊">
            <template #title>Активные опросы</template>
            
            <div v-if="settingsStore.activePolls.length > 0" class="divide-y divide-gray-100">
              <div v-for="poll in settingsStore.activePolls" :key="poll.id" class="py-4 flex items-center justify-between">
                <div>
                  <strong>Опрос #{{ poll.id.slice(0, 8) }}</strong>
                  <p class="text-sm text-gray-500 mt-1">Chat: {{ poll.chat_id }}</p>
                </div>
              </div>
            </div>
            <div v-else class="text-gray-500 text-center py-8">
              Нет активных опросов
            </div>
          </DashboardCard>
          
          <!-- Администраторы -->
          <DashboardCard icon="👥">
            <template #title>Администраторы</template>
            
            <AdminList 
              :admin-ids="settingsStore.adminIds"
              @add="handleAddAdmin"
              @remove="handleRemoveAdmin"
            />
          </DashboardCard>
        </div>
      </main>
    </div>
    
    <!-- Модальное окно для добавления/редактирования расписания -->
    <div v-if="showAddSchedule || editingSchedule" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click="closeModal">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-auto" @click.stop>
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white">
          <h2 class="text-lg font-semibold">{{ editingSchedule ? 'Редактировать расписание' : 'Новое расписание' }}</h2>
          <button @click="closeModal" class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors">✕</button>
        </div>
        
        <ScheduleForm
          :schedule="editingSchedule"
          :is-edit="!!editingSchedule"
          @submit="handleScheduleSubmit"
          @cancel="closeModal"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import Sidebar from '@/components/Sidebar.vue'
import Topbar from '@/components/Topbar.vue'
import DashboardCard from '@/components/DashboardCard.vue'
import TemplateForm from '@/components/TemplateForm.vue'
import ScheduleItem from '@/components/ScheduleItem.vue'
import ScheduleForm from '@/components/ScheduleForm.vue'
import AdminList from '@/components/AdminList.vue'

const settingsStore = useSettingsStore()

const showAddSchedule = ref(false)
const editingSchedule = ref(null)

onMounted(async () => {
  await Promise.all([
    settingsStore.loadTemplate(),
    settingsStore.loadSchedules(),
    settingsStore.loadActivePolls(),
    settingsStore.loadAdminIds()
  ])
})

// Template
const handleSaveTemplate = async (templateData) => {
  const success = await settingsStore.saveTemplate(templateData)
  if (success) {
    alert('Шаблон сохранён!')
  } else {
    alert('Ошибка сохранения')
  }
}

// Schedules
const handleEditSchedule = (schedule) => {
  editingSchedule.value = schedule
  showAddSchedule.value = false
}

const handleDeleteSchedule = async (id) => {
  if (!confirm('Удалить это расписание?')) return
  
  const success = await settingsStore.deleteSchedule(id)
  if (!success) {
    alert('Ошибка удаления')
  }
}

const handleScheduleSubmit = async (scheduleData) => {
  let success
  
  if (editingSchedule.value) {
    success = await settingsStore.updateSchedule(editingSchedule.value.id, scheduleData)
  } else {
    success = await settingsStore.addSchedule(scheduleData)
  }
  
  if (success) {
    closeModal()
  } else {
    alert('Ошибка сохранения')
  }
}

const closeModal = () => {
  showAddSchedule.value = false
  editingSchedule.value = null
}

// Admins
const handleAddAdmin = async (adminId) => {
  const success = await settingsStore.addAdminId(adminId)
  if (!success) {
    alert('Ошибка добавления администратора')
  }
}

const handleRemoveAdmin = async (adminId) => {
  if (!confirm(`Удалить администратора ${adminId}?`)) return
  
  const success = await settingsStore.removeAdminId(adminId)
  if (!success) {
    alert('Ошибка удаления')
  }
}
</script>
