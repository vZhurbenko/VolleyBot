import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const template = ref(null)
  const schedules = ref([])
  const activePolls = ref([])
  const adminIds = ref([])
  const adminCount = ref(0)
  const isLoading = ref(false)

  // Template
  async function loadTemplate() {
    try {
      const response = await fetch('/api/admin/settings/template', {
        credentials: 'include'
      })
      if (response.ok) {
        template.value = await response.json()
      }
    } catch (error) {
      console.error('Ошибка загрузки шаблона:', error)
    }
  }

  async function saveTemplate(templateData) {
    const response = await fetch('/api/admin/settings/template', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(templateData)
    })
    if (response.ok) {
      await loadTemplate()
      return true
    }
    return false
  }

  // Schedules
  async function loadSchedules() {
    try {
      const response = await fetch('/api/admin/settings/schedules', {
        credentials: 'include'
      })
      if (response.ok) {
        schedules.value = await response.json()
      }
    } catch (error) {
      console.error('Ошибка загрузки расписаний:', error)
    }
  }

  async function addSchedule(scheduleData) {
    const response = await fetch('/api/admin/settings/schedules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(scheduleData)
    })
    if (response.ok) {
      await loadSchedules()
      return true
    }
    return false
  }

  async function updateSchedule(id, scheduleData) {
    const response = await fetch(`/api/admin/settings/schedules/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(scheduleData)
    })
    if (response.ok) {
      await loadSchedules()
      return true
    }
    return false
  }

  async function deleteSchedule(id) {
    const response = await fetch(`/api/admin/settings/schedules/${id}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    if (response.ok) {
      await loadSchedules()
      return true
    }
    return false
  }

  // Active Polls
  async function loadActivePolls() {
    try {
      const response = await fetch('/api/admin/settings/active_polls', {
        credentials: 'include'
      })
      if (response.ok) {
        activePolls.value = await response.json()
      }
    } catch (error) {
      console.error('Ошибка загрузки опросов:', error)
    }
  }

  // Admin IDs
  async function loadAdminIds() {
    try {
      const response = await fetch('/api/admin/settings/admin_ids', {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        adminIds.value = data.admin_ids || []
      }
    } catch (error) {
      console.error('Ошибка загрузки админов:', error)
    }
  }

  async function addAdminId(adminId) {
    const response = await fetch('/api/admin/settings/admin_ids', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ admin_id: parseInt(adminId) })
    })
    if (response.ok) {
      await loadAdminIds()
      return true
    }
    return false
  }

  async function removeAdminId(adminId) {
    const response = await fetch(`/api/admin/settings/admin_ids/${adminId}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    if (response.ok) {
      await loadAdminIds()
      return true
    }
    return false
  }

  // Stats
  async function loadAdminCount() {
    try {
      const response = await fetch('/api/admin/stats', {
        credentials: 'include'
      })
      if (response.ok) {
        const data = await response.json()
        adminCount.value = data.admin_count || 0
      }
    } catch (error) {
      console.error('Ошибка загрузки статистики администраторов:', error)
    }
  }

  return {
    template,
    schedules,
    activePolls,
    adminIds,
    adminCount,
    isLoading,
    loadTemplate,
    saveTemplate,
    loadSchedules,
    addSchedule,
    updateSchedule,
    deleteSchedule,
    loadActivePolls,
    loadAdminIds,
    addAdminId,
    removeAdminId,
    loadAdminCount
  }
})
