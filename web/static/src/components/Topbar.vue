<template>
  <header class="bg-white border-b border-gray-200">
    <div class="flex items-center justify-between max-w-7xl mx-auto px-6 py-4">
      <h1 class="text-xl font-bold text-gray-900">
        <slot name="title">VolleyBot Admin</slot>
      </h1>

      <div class="flex items-center gap-4">
        <img
          v-if="user?.photo_url"
          :src="user.photo_url"
          alt="User"
          class="w-10 h-10 rounded-full border-2 border-gray-300"
        />
        <div v-else class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold">
          {{ userInitials }}
        </div>

        <span class="text-gray-700 font-medium">
          {{ user?.first_name }} {{ user?.last_name || '' }}
        </span>

        <button @click="handleLogout" class="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors">
          Выйти
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const user = computed(() => authStore.user)

const userInitials = computed(() => {
  if (!user.value) return '?'
  const first = user.value.first_name?.[0] || ''
  const last = user.value.last_name?.[0] || ''
  return (first + last).toUpperCase()
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/')
}
</script>
