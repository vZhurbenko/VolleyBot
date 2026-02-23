<template>
  <div class="bg-white rounded shadow p-4 lg:p-6 mb-6">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <!-- Кнопка меню для мобильных -->
        <button
          @click="toggleMenu"
          class="lg:hidden p-2 rounded hover:bg-gray-100 transition-colors"
        >
          <span class="text-xl">☰</span>
        </button>

        <h1 class="text-lg lg:text-xl font-bold text-gray-900">
          <slot name="title">Team R Admin</slot>
        </h1>
      </div>

      <div class="flex items-center gap-2 lg:gap-4">
        <img
          v-if="user?.photo_url"
          :src="user.photo_url"
          alt="User"
          class="w-8 h-8 lg:w-10 lg:h-10 rounded-full border-2 border-gray-300"
        />
        <div
          v-else
          class="w-8 h-8 lg:w-10 lg:h-10 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold"
        >
          {{ userInitials }}
        </div>

        <span class="hidden md:block text-gray-700 font-medium">
          {{ user?.first_name }} {{ user?.last_name || "" }}
        </span>

        <button
          @click="handleLogout"
          class="px-3 py-1.5 lg:px-4 lg:py-2 text-sm text-red-600 hover:text-red-700 rounded transition-colors"
        >
          <span class="hidden md:inline">Выйти</span>
          <span class="md:hidden">✕</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";

const authStore = useAuthStore();
const router = useRouter();

const user = computed(() => authStore.user);

const userInitials = computed(() => {
  if (!user.value) return "?";
  const first = user.value.first_name?.[0] || "";
  const last = user.value.last_name?.[0] || "";
  return (first + last).toUpperCase();
});

const handleLogout = async () => {
  await authStore.logout();
  router.push("/");
};

const toggleMenu = () => {
  window.dispatchEvent(new CustomEvent('toggle-menu'));
};
</script>
