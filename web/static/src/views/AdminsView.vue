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
          <div class="flex items-center gap-3">
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
            <div>
              <p class="font-medium text-gray-900">
                {{ user.first_name }} {{ user.last_name || '' }}
                <span v-if="user.username" class="text-gray-400 font-normal">@{{ user.username }}</span>
              </p>
              <p class="text-sm text-gray-500">ID: {{ user.telegram_id }}</p>
              <p v-if="!user.is_active" class="text-xs text-red-500 font-medium">Деактивирован</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="user.is_admin" class="px-3 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
              Админ
            </span>
            <button
              v-if="!user.is_admin && user.is_active"
              @click="handleMakeAdmin(user.telegram_id)"
              class="px-3 py-1.5 rounded text-sm font-medium transition-colors bg-purple-100 text-purple-700 hover:bg-purple-200"
            >
              Сделать админом
            </button>
            <button
              v-if="user.is_admin && user.is_active"
              @click="handleRemoveAdmin(user.telegram_id)"
              class="px-3 py-1.5 rounded text-sm font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
            >
              Снять права
            </button>
            <button
              @click="handleToggleActive(user.telegram_id, user.is_active)"
              class="px-3 py-1.5 rounded text-sm font-medium transition-colors"
              :class="user.is_active ? 'bg-orange-100 text-orange-700 hover:bg-orange-200' : 'bg-green-100 text-green-700 hover:bg-green-200'"
            >
              {{ user.is_active ? 'Деактивировать' : 'Активировать' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const users = ref([])
const newTelegramId = ref('')
const loading = ref(false)

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
    console.log('Пользователи:', data)
    // API возвращает массив напрямую, а не объект {users: [...]}
    users.value = Array.isArray(data) ? data : (data.users || [])
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

const getInitials = (user) => {
  const first = user.first_name?.[0] || ''
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}
</script>
