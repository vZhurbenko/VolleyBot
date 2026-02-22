<template>
  <div
    class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4"
  >
    <div class="bg-white rounded-xl shadow-lg p-8 w-full max-w-md text-center">
      <div class="text-6xl mb-4">🏐</div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">VolleyBot</h1>
      <p class="text-gray-500 mb-6">Система управления тренировками</p>

      <div v-if="isAuthenticated" class="mt-6">
        <p class="text-green-600 font-medium mb-4">✓ Вы уже авторизованы</p>
        <button
          @click="goToAdmin"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
        >
          Перейти в админ-панель
        </button>
      </div>

      <div v-else class="mt-6">
        <div id="telegram-login" class="flex justify-center mb-6"></div>

        <div
          v-if="errorMessage"
          class="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm"
        >
          {{ errorMessage }}
        </div>
      </div>

      <div class="mt-8 text-gray-400 text-sm">VolleyBot © {{ new Date().getFullYear() }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const isAuthenticated = computed(() => authStore.isAuthenticated);
const user = computed(() => authStore.user);

const errorMessage = ref("");

onMounted(async () => {
  await authStore.checkAuth();
  loadTelegramConfig();
});

const loadTelegramConfig = async () => {
  try {
    const response = await fetch("/api/auth/telegram/config");
    const config = await response.json();
    initTelegramWidget(config.bot_username);
  } catch (error) {
    console.error("Ошибка загрузки конфигурации:", error);
    errorMessage.value = "Ошибка загрузки конфигурации Telegram";
  }
};

const initTelegramWidget = (botUsername) => {
  const script = document.createElement("script");
  script.src = "https://telegram.org/js/telegram-widget.js?22";
  script.setAttribute("data-telegram-login", botUsername);
  script.setAttribute("data-size", "large");
  script.setAttribute("data-radius", "3");
  script.setAttribute("data-lang", "ru");
  script.setAttribute("data-onauth", "onTelegramAuth(user)");
  script.setAttribute("data-request-access", "write");
  script.async = true;

  const container = document.getElementById("telegram-login");
  if (container) {
    container.appendChild(script);
  }
};

const onTelegramAuth = async (user) => {
  console.log("Telegram user data:", user);
  console.log("Начало авторизации...");

  try {
    const response = await fetch("/api/auth/telegram", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(user),
      credentials: "include",
    });

    console.log("Ответ сервера:", response.status);
    const result = await response.json();
    console.log("Результат:", result);

    if (response.ok && result.success) {
      console.log("Авторизация успешна, обновляем store...");
      // Обновляем auth store перед редиректом
      authStore.setUser(result.user);
      
      console.log("Переход на /admin через window.location...");
      // Используем window.location для гарантированного редиректа
      window.location.href = "/admin";
    } else {
      errorMessage.value = result.detail || "Ошибка авторизации";
      console.error("Ошибка авторизации:", errorMessage.value);
      if (response.status === 403) {
        const loginWidget = document.getElementById("telegram-login");
        if (loginWidget) {
          loginWidget.classList.add("hidden");
        }
      }
    }
  } catch (error) {
    console.error("Ошибка:", error);
    errorMessage.value = "Ошибка соединения с сервером";
  }
};

const goToAdmin = () => {
  router.push("/admin");
};

// Делаем функцию доступной глобально для Telegram виджета
window.onTelegramAuth = onTelegramAuth;
</script>
