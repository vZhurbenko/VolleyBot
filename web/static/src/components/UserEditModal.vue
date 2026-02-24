<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click="$emit('close')">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
      <!-- Заголовок -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">Редактировать пользователя</h3>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center rounded hover:bg-gray-100">
          <X class="w-5 h-5 text-gray-600" />
        </button>
      </div>

      <!-- Контент -->
      <div class="p-6 space-y-4">
        <!-- Информация о пользователе -->
        <div class="flex items-center gap-3 pb-4 border-b border-gray-100">
          <img
            v-if="user.photo_url"
            :src="user.photo_url"
            alt=""
            class="w-12 h-12 rounded-full"
          />
          <div
            v-else
            class="w-12 h-12 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold"
          >
            {{ getInitials(user) }}
          </div>
          <div>
            <p class="font-medium text-gray-900">
              {{ user.first_name }} {{ user.last_name || '' }}
            </p>
            <p v-if="user.username" class="text-sm text-gray-500">@{{ user.username }}</p>
            <p class="text-xs text-gray-400">ID: {{ user.telegram_id }}</p>
          </div>
        </div>

        <!-- Переключатель Администратор -->
        <div class="flex items-center justify-between">
          <div>
            <p class="font-medium text-gray-900">Администратор</p>
            <p class="text-sm text-gray-500">Права администратора</p>
          </div>
          <button
            @click="toggleAdmin"
            class="relative w-12 h-6 rounded-full transition-colors"
            :class="user.is_admin ? 'bg-teal-600' : 'bg-gray-300'"
          >
            <span
              class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform"
              :class="user.is_admin ? 'translate-x-6' : 'translate-x-0'"
            />
          </button>
        </div>

        <!-- Переключатель Активен -->
        <div class="flex items-center justify-between">
          <div>
            <p class="font-medium text-gray-900">Активен</p>
            <p class="text-sm text-gray-500">Доступ к системе</p>
          </div>
          <button
            @click="toggleActive"
            class="relative w-12 h-6 rounded-full transition-colors"
            :class="user.is_active ? 'bg-teal-600' : 'bg-gray-300'"
          >
            <span
              class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform"
              :class="user.is_active ? 'translate-x-6' : 'translate-x-0'"
            />
          </button>
        </div>

        <!-- Кнопка удаления -->
        <div class="pt-4 border-t border-gray-100">
          <button
            @click="$emit('delete', user)"
            class="w-full h-11 px-6 rounded font-medium transition-colors text-red-600 hover:text-red-700 bg-transparent"
          >
            Удалить пользователя
          </button>
        </div>
      </div>

      <!-- Кнопки действий -->
      <div class="px-6 py-4 bg-gray-50 rounded-b-lg flex flex-col sm:flex-row gap-2">
        <button
          @click="$emit('close')"
          class="flex-1 h-11 px-6 rounded font-medium transition-colors bg-gray-200 text-gray-700 hover:bg-gray-300"
        >
          Отмена
        </button>
        <button
          @click="handleSave"
          class="flex-1 h-11 px-6 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
        >
          Сохранить
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'save', 'delete'])

// Локальные копии для редактирования
const localUser = ref({ ...props.user })

const toggleAdmin = () => {
  localUser.value.is_admin = !localUser.value.is_admin
}

const toggleActive = () => {
  localUser.value.is_active = !localUser.value.is_active
}

const handleSave = () => {
  emit('save', localUser.value)
}

const getInitials = (user) => {
  const first = user.first_name?.[0] || ''
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase() || '?'
}
</script>
