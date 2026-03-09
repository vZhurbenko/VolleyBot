<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Игры</h1>
      <button
        v-if="authStore.isAdmin"
        @click="openAddGameModal"
        class="px-4 py-2 bg-teal-600 text-white rounded hover:bg-teal-700 transition-colors flex items-center gap-2"
      >
        <span>Добавить игру</span>
      </button>
    </div>

    <!-- Статистика -->
    <div v-if="gameStats.total > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-gray-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-gray-900">{{ gameStats.total }}</div>
        <div class="text-sm text-gray-600 mt-1">Всего игр</div>
      </div>
      <div class="bg-green-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-green-700">{{ gameStats.wins }}</div>
        <div class="text-sm text-green-600 mt-1">Побед</div>
      </div>
      <div class="bg-red-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-red-700">{{ gameStats.losses }}</div>
        <div class="text-sm text-red-600 mt-1">Поражений</div>
      </div>
      <div class="bg-yellow-50 rounded-lg p-4 text-center">
        <div class="text-2xl font-bold text-yellow-700">{{ gameStats.draws }}</div>
        <div class="text-sm text-yellow-600 mt-1">Ничьих</div>
      </div>
    </div>

    <!-- Фильтр по месяцу -->
    <div class="flex flex-wrap gap-4 mb-6">
      <div class="flex items-center gap-2">
        <button
          @click="previousMonth"
          class="p-2 rounded hover:bg-gray-100 transition-colors"
          title="Предыдущий месяц"
        >
          <ChevronLeft class="w-5 h-5" />
        </button>
        <span class="text-lg font-medium text-gray-900 min-w-[200px] text-center">
          {{ monthName(currentMonth) }} {{ currentYear }}
        </span>
        <button
          @click="nextMonth"
          class="p-2 rounded hover:bg-gray-100 transition-colors"
          title="Следующий месяц"
        >
          <ChevronRight class="w-5 h-5" />
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500">Загрузка...</div>

    <div v-else-if="games.length === 0" class="text-center py-8 text-gray-500">
      Нет игр на этот месяц
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="game in sortedGames"
        :key="game.id"
        class="border border-gray-200 rounded-lg p-3"
        :class="getGameStatusClass(game)"
      >
        <div class="flex items-center gap-4">
          <!-- Информация об игре -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-base font-semibold text-gray-900 truncate">
                {{ game.name }}
              </h3>
              <span v-if="game.opponent" class="text-sm text-gray-600 truncate"
                >vs {{ game.opponent }}</span
              >
            </div>
            <div class="flex items-center gap-3 text-xs text-gray-500">
              <div class="flex items-center gap-1">
                <Calendar class="w-3.5 h-3.5" />
                <span>{{ formatCompactDate(game.date) }}</span>
              </div>
              <div v-if="game.start_time" class="flex items-center gap-1">
                <Clock class="w-3.5 h-3.5" />
                <span>{{ game.start_time }}</span>
              </div>
              <div v-if="game.location" class="flex items-center gap-1">
                <MapPin class="w-3.5 h-3.5" />
                <span class="truncate">{{ game.location }}</span>
              </div>
            </div>
          </div>

          <!-- Результат или количество записавшихся -->
          <div class="flex items-center gap-4">
            <div
              v-if="game.result"
              class="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium"
              :class="getResultClass(game.result)"
            >
              <Trophy class="w-3.5 h-3.5" />
              <span>{{ getResultText(game.result) }} {{ game.score }}</span>
            </div>
            <div v-else class="text-sm text-gray-600">
              <span class="font-medium">{{ game.signups?.length || 0 }}</span> запис.
            </div>

            <!-- Кнопка записи -->
            <button
              @click="toggleSignup(game)"
              class="px-3 py-1.5 rounded text-sm font-medium transition-colors"
              :class="getUserSignupClass(game)"
            >
              {{ getUserSignupText(game) }}
            </button>

            <!-- Кнопки для админа -->
            <template v-if="authStore.isAdmin">
              <button
                @click="openEditGameModal(game)"
                class="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                title="Редактировать"
              >
                <Edit class="w-4 h-4" />
              </button>
              <button
                @click="openResultModal(game)"
                class="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors"
                title="Добавить результат"
              >
                <Trophy class="w-4 h-4" />
              </button>
              <button
                @click="deleteGame(game)"
                class="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                title="Удалить"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </template>
          </div>
        </div>

        <!-- Список записавшихся (компактный) -->
        <div
          v-if="game.signups && game.signups.length > 0"
          class="mt-2 pt-2 border-t border-gray-100"
        >
          <div class="flex flex-wrap gap-2">
            <div
              v-for="signup in game.signups"
              :key="signup.id"
              class="inline-flex items-center gap-1.5 px-2 py-1 bg-gray-100 rounded text-xs text-gray-700"
            >
              <div v-if="signup.photo_url" class="w-4 h-4 rounded-full overflow-hidden">
                <img :src="signup.photo_url" alt="" class="w-full h-full object-cover" />
              </div>
              <div
                v-else
                class="w-4 h-4 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 font-bold text-[10px]"
              >
                {{ getInitials(signup) }}
              </div>
              <span>{{ signup.first_name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка добавления/редактирования игры -->
    <GameForm v-if="showGameForm" :game="selectedGame" @close="closeGameForm" @save="saveGame" />

    <!-- Модалка результата -->
    <GameResultModal
      v-if="showResultModal"
      :game="selectedGame"
      @close="closeResultModal"
      @save="saveResult"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import {
  Plus,
  ChevronLeft,
  ChevronRight,
  Calendar,
  Clock,
  MapPin,
  Trophy,
  Edit,
  Trash2,
} from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";
import { useConfirmStore } from "@/stores/confirm";
import GameForm from "@/components/GameForm.vue";
import GameResultModal from "@/components/GameResultModal.vue";

const router = useRouter();
const authStore = useAuthStore();
const notificationsStore = useNotificationsStore();
const confirmStore = useConfirmStore();

const games = ref([]);
const allGames = ref([]);
const loading = ref(false);
const selectedGame = ref(null);
const showGameForm = ref(false);
const showResultModal = ref(false);

const now = new Date();
const currentYear = ref(now.getFullYear());
const currentMonth = ref(now.getMonth() + 1);

const monthNames = [
  "Январь",
  "Февраль",
  "Март",
  "Апрель",
  "Май",
  "Июнь",
  "Июль",
  "Август",
  "Сентябрь",
  "Октябрь",
  "Ноябрь",
  "Декабрь",
];

const monthName = (month) => monthNames[month - 1];

const sortedGames = computed(() => {
  return [...games.value].sort((a, b) => {
    const dateA = new Date(a.date + (a.start_time ? "T" + a.start_time : ""));
    const dateB = new Date(b.date + (b.start_time ? "T" + b.start_time : ""));
    return dateA - dateB;
  });
});

const gameStats = computed(() => {
  const allGamesList = allGames.value || [];
  const gamesWithResult = allGamesList.filter((g) => g.result);

  return {
    total: allGamesList.length,
    wins: gamesWithResult.filter((g) => g.result === "win").length,
    losses: gamesWithResult.filter((g) => g.result === "loss").length,
    draws: gamesWithResult.filter((g) => g.result === "draw").length,
  };
});

onMounted(async () => {
  if (authStore.isLoading) {
    await authStore.checkAuth();
  }

  if (!authStore.isAuthenticated) {
    router.push("/login?redirect=" + encodeURIComponent(router.currentRoute.value.fullPath));
    return;
  }

  loadGames();
});

const loadGames = async () => {
  loading.value = true;

  try {
    // Загружаем все игры (без ограничения по месяцу для статистики)
    const response = await fetch(
      `/api/games?year=${currentYear.value}&month=${currentMonth.value}`,
      {
        credentials: "include",
      },
    );

    if (!response.ok) {
      throw new Error("Failed to load games");
    }

    const data = await response.json();

    // Для каждой игры загружаем записавшихся
    for (const game of data.games || []) {
      const gameResponse = await fetch(`/api/games/${game.id}`, {
        credentials: "include",
      });
      if (gameResponse.ok) {
        const gameData = await gameResponse.json();
        game.signups = gameData.game?.signups || [];
      }
    }

    games.value = data.games || [];

    // Загружаем все игры для статистики за все время
    await loadAllGamesForStats();
  } catch (error) {
    console.error("Error loading games:", error);
    notificationsStore.error("Ошибка загрузки игр");
  } finally {
    loading.value = false;
  }
};

const loadAllGamesForStats = async () => {
  try {
    const response = await fetch(`/api/games`, {
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Failed to load all games");
    }

    const data = await response.json();
    allGames.value = data.games || [];
  } catch (error) {
    console.error("Error loading all games for stats:", error);
  }
};

const previousMonth = () => {
  currentMonth.value--;
  if (currentMonth.value < 1) {
    currentMonth.value = 12;
    currentYear.value--;
  }
  loadGames();
};

const nextMonth = () => {
  currentMonth.value++;
  if (currentMonth.value > 12) {
    currentMonth.value = 1;
    currentYear.value++;
  }
  loadGames();
};

const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    weekday: "short",
  });
};

const formatCompactDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    weekday: "short",
  });
};

const getInitials = (user) => {
  const first = user.first_name?.charAt(0) || "";
  const last = user.last_name?.charAt(0) || "";
  return (first + last).toUpperCase();
};

const getGameStatusClass = (game) => {
  const gameDate = new Date(game.date);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (gameDate < today) {
    return "bg-gray-50";
  }
  return "bg-white";
};

const getResultClass = (result) => {
  switch (result) {
    case "win":
      return "bg-green-100 text-green-800";
    case "loss":
      return "bg-red-100 text-red-800";
    case "draw":
      return "bg-yellow-100 text-yellow-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

const getResultText = (result) => {
  switch (result) {
    case "win":
      return "Победа";
    case "loss":
      return "Поражение";
    case "draw":
      return "Ничья";
    default:
      return result;
  }
};

const getUserSignupClass = (game) => {
  const isSignedUp = game.signups?.some((s) => s.user_telegram_id === authStore.user?.telegram_id);
  if (isSignedUp) {
    return "text-red-600 hover:text-red-700 bg-transparent";
  }
  return "bg-teal-100 text-teal-700 hover:bg-teal-200";
};

const getUserSignupText = (game) => {
  const isSignedUp = game.signups?.some((s) => s.user_telegram_id === authStore.user?.telegram_id);
  if (isSignedUp) {
    return "Выписаться";
  }
  return "Записаться";
};

const toggleSignup = async (game) => {
  try {
    const response = await fetch(`/api/games/${game.id}/signup`, {
      method: "POST",
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Failed to toggle signup");
    }

    const result = await response.json();

    if (result.success) {
      notificationsStore.success(
        result.action === "registered" ? "Вы записаны на игру" : "Запись отменена",
      );
      loadGames();
    }
  } catch (error) {
    console.error("Error toggling signup:", error);
    notificationsStore.error("Ошибка записи на игру");
  }
};

const openAddGameModal = () => {
  selectedGame.value = null;
  showGameForm.value = true;
};

const openEditGameModal = (game) => {
  selectedGame.value = { ...game };
  showGameForm.value = true;
};

const closeGameForm = () => {
  showGameForm.value = false;
  selectedGame.value = null;
};

const saveGame = async (gameData) => {
  try {
    const url = selectedGame.value
      ? `/api/admin/games/${selectedGame.value.id}`
      : "/api/admin/games";

    const method = selectedGame.value ? "PUT" : "POST";

    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(gameData),
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to save game");
    }

    notificationsStore.success(selectedGame.value ? "Игра обновлена" : "Игра создана");
    closeGameForm();
    loadGames();
  } catch (error) {
    console.error("Error saving game:", error);
    notificationsStore.error(error.message || "Ошибка сохранения игры");
  }
};

const deleteGame = async (game) => {
  const confirmed = await confirmStore.danger(
    `Вы уверены, что хотите удалить игру "${game.name}"?`,
  );

  if (!confirmed) return;

  try {
    const response = await fetch(`/api/admin/games/${game.id}`, {
      method: "DELETE",
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Failed to delete game");
    }

    notificationsStore.success("Игра удалена");
    loadGames();
  } catch (error) {
    console.error("Error deleting game:", error);
    notificationsStore.error("Ошибка удаления игры");
  }
};

const openResultModal = (game) => {
  selectedGame.value = { ...game };
  showResultModal.value = true;
};

const closeResultModal = () => {
  showResultModal.value = false;
  selectedGame.value = null;
};

const saveResult = async (resultData) => {
  try {
    // Если результат пустой — удаляем его
    if (!resultData.result || !resultData.score) {
      const response = await fetch(`/api/admin/games/${selectedGame.value.id}/result`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to clear result");
      }

      notificationsStore.success("Результат сброшен");
      closeResultModal();
      loadGames();
      return;
    }

    const response = await fetch(`/api/admin/games/${selectedGame.value.id}/result`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(resultData),
      credentials: "include",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to save result");
    }

    notificationsStore.success("Результат сохранён");
    closeResultModal();
    loadGames();
  } catch (error) {
    console.error("Error saving result:", error);
    notificationsStore.error(error.message || "Ошибка сохранения результата");
  }
};
</script>
