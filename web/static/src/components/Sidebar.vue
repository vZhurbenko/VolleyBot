<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import {
  LayoutDashboard,
  Calendar,
  FileText,
  ClipboardList,
  Users,
  Link,
  X,
  LogOut
} from 'lucide-vue-next'
import logo from '@/img/logo.svg'

const authStore = useAuthStore()
const router = useRouter()

const emit = defineEmits(['menu-change'])

const isOpen = ref(false)

const user = computed(() => authStore.user)

const userName = computed(() => {
  if (!user.value) return '';
  return user.value.first_name || '';
});

const userUsername = computed(() => {
  if (!user.value) return '';
  return user.value.username || '';
});

const handleLogout = async () => {
  await authStore.logout();
  router.push('/');
};

const handleToggleMenu = () => {
  isOpen.value = !isOpen.value
  // Блокируем прокрутку body при открытом меню
  document.body.style.overflow = isOpen.value ? 'hidden' : ''
}

// Отправляем состояние меню родителю
watch(isOpen, (newValue) => {
  emit('menu-change', newValue)
})

onMounted(() => {
  window.addEventListener('toggle-menu', handleToggleMenu)
})

onUnmounted(() => {
  window.removeEventListener('toggle-menu', handleToggleMenu)
  // Сбрасываем блокировку прокрутки
  document.body.style.overflow = ''
})
</script>

<template>
  <!-- Overlay для мобильных -->
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black/50 z-40 lg:hidden"
    @click="isOpen = false"
  ></div>

  <!-- Sidebar -->
  <aside
    :class="[
      'fixed lg:relative inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 flex flex-col transform transition-transform duration-300 lg:transform-none lg:h-full',
      isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
    ]"
  >
    <div class="p-4 flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-3">
        <img :src="logo" alt="Team R Logo" class="w-10 h-10" />
        <span class="text-xl font-bold text-gray-900">Team R</span>
      </div>
      <!-- Кнопка закрытия для мобильных -->
      <button
        @click="isOpen = false"
        class="lg:hidden p-2 rounded hover:bg-gray-100"
      >
        <X class="w-5 h-5" />
      </button>
    </div>

    <nav class="flex-1 px-4 pb-4 flex flex-col gap-2 overflow-y-auto">
      <!-- Меню для администраторов -->
      <template v-if="authStore.isAdmin">
        <router-link
          to="/dashboard"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'dashboard' }"
          @click="isOpen = false"
        >
          <LayoutDashboard class="w-5 h-5" />
          <span class="font-medium">Дашборд</span>
        </router-link>
        <router-link
          to="/dashboard/calendar"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'calendar' }"
          @click="isOpen = false"
        >
          <Calendar class="w-5 h-5" />
          <span class="font-medium">Календарь</span>
        </router-link>
        <router-link
          to="/dashboard/my-trainings"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'my-trainings' }"
          @click="isOpen = false"
        >
          <FileText class="w-5 h-5" />
          <span class="font-medium">Мои тренировки</span>
        </router-link>
        <router-link
          to="/dashboard/schedules"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'schedules' }"
          @click="isOpen = false"
        >
          <ClipboardList class="w-5 h-5" />
          <span class="font-medium">Расписания</span>
        </router-link>
        <router-link
          to="/dashboard/users"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'users' }"
          @click="isOpen = false"
        >
          <Users class="w-5 h-5" />
          <span class="font-medium">Пользователи</span>
        </router-link>
        <router-link
          to="/dashboard/invites"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'invites' }"
          @click="isOpen = false"
        >
          <Link class="w-5 h-5" />
          <span class="font-medium">Приглашения</span>
        </router-link>
        <router-link
          to="/dashboard/trainings"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'trainings' }"
          @click="isOpen = false"
        >
          <FileText class="w-5 h-5" />
          <span class="font-medium">Записи</span>
        </router-link>
        <router-link
          to="/dashboard/template"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'template' }"
          @click="isOpen = false"
        >
          <FileText class="w-5 h-5" />
          <span class="font-medium">Шаблон</span>
        </router-link>
      </template>

      <!-- Меню для обычных пользователей -->
      <template v-else>
        <router-link
          to="/dashboard/calendar"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'calendar' }"
          @click="isOpen = false"
        >
          <Calendar class="w-5 h-5" />
          <span class="font-medium">Календарь</span>
        </router-link>
        <router-link
          to="/dashboard/my-trainings"
          class="flex items-center gap-3 px-4 py-3 rounded text-gray-600 hover:bg-teal-50 hover:text-teal-700 transition-colors"
          :class="{ 'bg-teal-50 text-teal-700': $route.name === 'my-trainings' }"
          @click="isOpen = false"
        >
          <FileText class="w-5 h-5" />
          <span class="font-medium">Мои тренировки</span>
        </router-link>
      </template>
    </nav>

    <!-- Информация о пользователе внизу сайдбара -->
    <div class="border-t border-gray-200 p-4 flex-shrink-0">
      <div class="flex items-center gap-3">
        <img
          v-if="user?.photo_url"
          :src="user.photo_url"
          alt="User"
          class="w-10 h-10 rounded-full border-2 border-gray-300 flex-shrink-0"
        />
        <div
          v-else
          class="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold flex-shrink-0"
        >
          {{ userName.charAt(0).toUpperCase() }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate">
            {{ userName }}
          </p>
          <p v-if="userUsername" class="text-xs text-gray-500 truncate">
            @{{ userUsername }}
          </p>
        </div>
        <button
          @click="handleLogout"
          class="p-2 text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0"
          title="Выйти"
        >
          <LogOut class="w-5 h-5" />
        </button>
      </div>
    </div>
  </aside>
</template>
