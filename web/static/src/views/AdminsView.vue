<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Пользователи</h1>

    <div class="flex flex-col gap-6">
      <!-- Форма добавления -->
      <div class="flex flex-col gap-2">
        <label class="block text-sm font-medium text-gray-700">Добавить пользователя по Telegram ID</label>
        <div class="flex flex-col sm:flex-row gap-2">
          <input
            v-model="newTelegramId"
            type="number"
            class="flex-1 h-11 px-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 transition-colors"
            placeholder="Telegram ID"
          />
          <button @click="handleAdd" class="h-11 px-6 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700 whitespace-nowrap">
            Добавить
          </button>
        </div>
      </div>

      <!-- Список пользователей -->
      <div v-if="loading" class="text-center py-8 text-gray-500">
        Загрузка...
      </div>

      <div v-else-if="users.length === 0" class="text-gray-500 text-center py-8">
        Нет пользователей
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="user in users"
          :key="user.telegram_id"
          class="flex items-center justify-between py-3 px-4 rounded"
          :class="user.is_active ? 'bg-gray-50' : 'bg-gray-100 opacity-60'"
        >
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <img
              v-if="user.photo_url"
              :src="user.photo_url"
              alt=""
              class="w-10 h-10 rounded-full"
            />
            <div
              v-else
              class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold"
            >
              {{ getInitials(user) }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <p class="font-medium text-gray-900 truncate">
                  {{ user.first_name }} {{ user.last_name || '' }}
                  <span v-if="user.username" class="text-gray-400 font-normal">@{{ user.username }}</span>
                </p>
                <Shield
                  v-if="user.is_admin"
                  class="w-4 h-4 text-purple-600 flex-shrink-0"
                  title="Администратор"
                />
              </div>
              <p class="text-sm text-gray-500">ID: {{ user.telegram_id }}</p>
              <p v-if="!user.is_active" class="text-xs text-red-500 font-medium">Деактивирован</p>
            </div>
          </div>
          <button
            @click="openEditModal(user)"
            class="w-9 h-9 flex items-center justify-center rounded hover:bg-gray-200 transition-colors flex-shrink-0 ml-2"
            title="Редактировать"
          >
            <Edit2 class="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>
    </div>

    <!-- Модалка редактирования -->
    <UserEditModal
      v-if="showEditModal && editingUser"
      :user="editingUser"
      @close="closeEditModal"
      @save="handleSaveUser"
      @delete="handleDeleteFromModal"
      @update:user="editingUser = $event"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Shield, Edit2 } from 'lucide-vue-next'
import UserEditModal from '@/components/UserEditModal.vue'

const users = ref([])
const newTelegramId = ref('')
const loading = ref(false)
const editingUser = ref(null)
const showEditModal = ref(false)

onMounted(() => {
  loadUsers()
})

const loadUsers = async () => {
  loading.value = true

  try {
    const response = await fetch('/api/admin/users', {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Ошибка загрузки' }))
      console.error('Ошибка API:', error)
      alert('Ошибка загрузки пользователей: ' + error.detail)
      return
    }

    const data = await response.json()
    // Сортировка:
    // 1. Админы активные
    // 2. Админы неактивные
    // 3. Обычные пользователи активные
    // 4. Обычные пользователи неактивные
    // Внутри групп — по имени
    users.value = data.sort((a, b) => {
      // Сначала админы
      if (a.is_admin && !b.is_admin) return -1
      if (!a.is_admin && b.is_admin) return 1
      // Потом активные
      if (a.is_active && !b.is_active) return -1
      if (!a.is_active && b.is_active) return 1
      // Потом по имени
      return (a.first_name || '').localeCompare(b.first_name || '')
    })
  } catch (error) {
    console.error('Error loading users:', error)
    alert('Ошибка сети: ' + error.message)
  } finally {
    loading.value = false
  }
}

const handleAdd = async () => {
  if (!newTelegramId.value) return
  
  try {
    const response = await fetch('/api/admin/users', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        telegram_id: parseInt(newTelegramId.value)
      })
    })
    
    const result = await response.json()
    
    if (response.ok && result.success) {
      newTelegramId.value = ''
      loadUsers()
      alert(result.message || 'Пользователь добавлен')
    } else {
      alert(result.detail || 'Ошибка добавления')
    }
  } catch (error) {
    console.error('Error adding user:', error)
    alert('Ошибка добавления пользователя')
  }
}

const handleToggleActive = async (telegramId, isActive) => {
  const actionText = isActive ? 'Деактивировать' : 'Активировать'
  if (!confirm(`${actionText} пользователя ID: ${telegramId}?`)) return

  try {
    const response = await fetch(`/api/admin/users/${telegramId}/toggle-active`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      loadUsers()
      alert(result.message || `Пользователь ${isActive ? 'деактивирован' : 'активирован'}`)
    } else {
      alert(result.detail || 'Ошибка')
    }
  } catch (error) {
    console.error('Error toggling active status:', error)
    alert('Ошибка изменения статуса')
  }
}

const handleMakeAdmin = async (telegramId) => {
  if (!confirm(`Сделать пользователя администратором?`)) return

  try {
    const response = await fetch('/api/admin/settings/admin_ids', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        admin_id: telegramId
      })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      loadUsers()
      alert(result.message || 'Пользователь стал администратором')
    } else {
      alert(result.detail || 'Ошибка назначения администратором')
    }
  } catch (error) {
    console.error('Error making admin:', error)
    alert('Ошибка назначения администратором')
  }
}

const handleRemoveAdmin = async (telegramId) => {
  if (!confirm(`Снять админские права у пользователя?`)) return

  try {
    const response = await fetch(`/api/admin/settings/admin_ids/${telegramId}`, {
      method: 'DELETE',
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      // Принудительно перезагружаем список
      await loadUsers()
      console.log('Пользователи после снятия прав:', users.value)
      alert(result.message || 'Администратор удалён')
    } else {
      alert(result.detail || 'Ошибка снятия админских прав')
    }
  } catch (error) {
    console.error('Error removing admin:', error)
    alert('Ошибка снятия админских прав')
  }
}

const handleDelete = async (telegramId, firstName) => {
  if (!confirm(`Полностью удалить пользователя "${firstName}"? Это действие необратимо.`)) return

  try {
    const response = await fetch(`/api/admin/users/${telegramId}`, {
      method: 'DELETE',
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      loadUsers()
      alert(result.message || 'Пользователь удалён')
    } else {
      alert(result.detail || 'Ошибка удаления')
    }
  } catch (error) {
    console.error('Error deleting user:', error)
    alert('Ошибка удаления пользователя')
  }
}

// Функции для модалки редактирования
const openEditModal = (user) => {
  editingUser.value = user
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
  editingUser.value = null
}

const handleSaveUser = async (updatedUser) => {
  const changes = []
  
  try {
    // Сравниваем с оригинальным пользователем из списка
    const originalUser = users.value.find(u => u.telegram_id === updatedUser.telegram_id)
    if (!originalUser) {
      throw new Error('Пользователь не найден')
    }
    
    // Проверяем изменения
    if (updatedUser.is_admin !== originalUser.is_admin) {
      if (updatedUser.is_admin) {
        changes.push('назначение администратором')
        const response = await fetch('/api/admin/settings/admin_ids', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({ admin_id: updatedUser.telegram_id })
        })
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Ошибка назначения администратором')
        }
      } else {
        changes.push('снятие администраторских прав')
        const response = await fetch(`/api/admin/settings/admin_ids/${updatedUser.telegram_id}`, {
          method: 'DELETE',
          credentials: 'include'
        })
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Ошибка снятия администраторских прав')
        }
      }
    }

    if (updatedUser.is_active !== originalUser.is_active) {
      changes.push(updatedUser.is_active ? 'активация' : 'деактивация')
      const response = await fetch(`/api/admin/users/${updatedUser.telegram_id}/toggle-active`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Ошибка изменения статуса')
      }
    }

    closeEditModal()
    await loadUsers()
  } catch (error) {
    console.error('Error saving user:', error)
    alert('Ошибка сохранения: ' + error.message)
  }
}

const handleDeleteFromModal = async (user) => {
  if (!confirm(`Полностью удалить пользователя "${user.first_name}"? Это действие необратимо.`)) return

  try {
    const response = await fetch(`/api/admin/users/${user.telegram_id}`, {
      method: 'DELETE',
      credentials: 'include'
    })

    const result = await response.json()

    if (response.ok && result.success) {
      closeEditModal()
      await loadUsers()
      alert(result.message || 'Пользователь удалён')
    } else {
      alert(result.detail || 'Ошибка удаления')
    }
  } catch (error) {
    console.error('Error deleting user:', error)
    alert('Ошибка удаления пользователя')
  }
}

const getInitials = (user) => {
  const first = user.first_name?.[0] || ''
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}
</script>
