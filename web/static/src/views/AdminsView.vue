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
          class="flex items-center justify-between py-3 px-4 bg-gray-50 rounded"
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
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="user.is_admin" class="px-3 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
              Админ
            </span>
            <button
              @click="handleRemove(user.telegram_id)"
              class="w-8 h-8 flex items-center justify-center rounded hover:bg-red-50 text-red-500 transition-colors"
              title="Деактивировать"
            >
              ✕
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

const handleRemove = async (telegramId) => {
  if (!confirm(`Деактивировать пользователя ID: ${telegramId}?`)) return
  
  try {
    const response = await fetch(`/api/admin/users/${telegramId}`, {
      method: 'DELETE',
      credentials: 'include'
    })
    
    const result = await response.json()
    
    if (response.ok && result.success) {
      loadUsers()
      alert(result.message || 'Пользователь деактивирован')
    } else {
      alert(result.detail || 'Ошибка удаления')
    }
  } catch (error) {
    console.error('Error removing user:', error)
    alert('Ошибка удаления пользователя')
  }
}

const getInitials = (user) => {
  const first = user.first_name?.[0] || ''
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}
</script>
