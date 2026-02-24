<template>
  <div class="bg-white rounded shadow p-4 lg:p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Приглашения</h1>
      <button
        @click="showCreateModal = true"
        class="px-4 py-2 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
      >
        Создать приглашение
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500">Загрузка...</div>

    <div v-else-if="codes.length === 0" class="text-gray-500 text-center py-8">
      Нет активных приглашений
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-200">
            <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">Код</th>
            <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">Создан</th>
            <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">Действует до</th>
            <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">Статус</th>
            <th class="text-right py-3 px-4 text-sm font-semibold text-gray-700">Действие</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="code in codes" :key="code.code" class="border-b border-gray-100">
            <td class="py-3 px-4">
              <code class="px-2 py-1 bg-gray-100 rounded text-sm font-mono">{{ code.code }}</code>
            </td>
            <td class="py-3 px-4 text-sm text-gray-700">
              {{ formatDate(code.created_at) }}
            </td>
            <td class="py-3 px-4 text-sm text-gray-700">
              {{ code.expires_at ? formatDate(code.expires_at) : "∞" }}
            </td>
            <td class="py-3 px-4">
              <span class="px-2 py-1 rounded text-xs font-medium" :class="getStatusClass(code)">
                {{ getStatusText(code) }}
              </span>
            </td>
            <td class="py-3 px-4 text-right">
              <button
                v-if="code.enabled && !code.used_by"
                @click="copyLink(code.code)"
                class="px-3 py-1.5 text-sm rounded font-medium transition-colors bg-teal-100 text-teal-700 hover:bg-teal-200"
              >
                Копировать
              </button>
              <button
                v-if="code.enabled && !code.used_by"
                @click="deactivateCode(code.code)"
                class="ml-2 px-3 py-1.5 text-sm rounded font-medium transition-colors bg-red-100 text-red-700 hover:bg-red-200"
              >
                Отозвать
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модалка создания -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click="showCreateModal = false"
    >
      <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
        <div class="px-6 py-4 border-b border-gray-100">
          <h3 class="text-lg font-semibold text-gray-900">Создать приглашение</h3>
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2"> Срок действия </label>
            <select
              v-model="selectedExpiresIn"
              class="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option :value="null">Бессрочно</option>
              <option :value="1">1 день</option>
              <option :value="7">7 дней</option>
              <option :value="30">30 дней</option>
            </select>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button
            @click="showCreateModal = false"
            class="px-4 py-2 rounded font-medium transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
          >
            Отмена
          </button>
          <button
            @click="createInviteCode"
            class="px-4 py-2 rounded font-medium transition-colors bg-teal-600 text-white hover:bg-teal-700"
          >
            Создать
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const codes = ref([]);
const loading = ref(false);
const showCreateModal = ref(false);
const selectedExpiresIn = ref(null);

onMounted(() => {
  loadCodes();
});

const loadCodes = async () => {
  loading.value = true;

  try {
    const response = await fetch("/api/admin/invite", {
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error("Failed to load codes");
    }

    const data = await response.json();
    codes.value = data.codes || [];
  } catch (error) {
    console.error("Error loading codes:", error);
  } finally {
    loading.value = false;
  }
};

const createInviteCode = async () => {
  try {
    const response = await fetch("/api/admin/invite", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({
        expires_in_days: selectedExpiresIn.value,
      }),
    });

    const result = await response.json();

    if (response.ok && result.success) {
      // Сначала показываем ссылку, потом пробуем копировать
      const url = `${window.location.origin}/invite/${result.code}`;

      // Пробуем скопировать
      try {
        await navigator.clipboard.writeText(url);
        alert(`Приглашение создано!\n\nСсылка: ${url}\n\nСкопировано в буфер обмена.`);
      } catch (copyError) {
        // Если не удалось скопировать, просто показываем ссылку
        alert(`Приглашение создано!\n\nСсылка:\n${url}\n\nСкопируйте её вручную.`);
      }

      showCreateModal.value = false;
      selectedExpiresIn.value = null;
      loadCodes();
    } else {
      alert(result.detail || "Ошибка создания");
    }
  } catch (error) {
    console.error("Error creating code:", error);
    alert("Ошибка создания приглашения");
  }
};

const deactivateCode = async (code) => {
  if (!confirm("Отозвать это приглашение?")) return;

  try {
    const response = await fetch(`/api/admin/invite/${code}`, {
      method: "DELETE",
      credentials: "include",
    });

    const result = await response.json();

    if (response.ok && result.success) {
      loadCodes();
      alert("Приглашение отозвано");
    } else {
      alert(result.detail || "Ошибка отзыва");
    }
  } catch (error) {
    console.error("Error deactivating code:", error);
    alert("Ошибка отзыва приглашения");
  }
};

const copyLink = async (code) => {
  const url = `${window.location.origin}/invite/${code}`;
  try {
    await navigator.clipboard.writeText(url);
    alert("Ссылка скопирована в буфер обмена!");
  } catch (error) {
    console.error("Error copying link:", error);
    alert("Не удалось скопировать ссылку");
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return "—";
  const date = new Date(dateStr);
  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getStatusClass = (code) => {
  if (!code.enabled) {
    return "bg-gray-100 text-gray-700";
  }
  if (code.used_by) {
    return "bg-gray-100 text-gray-700";
  }
  if (code.expires_at) {
    const expires = new Date(code.expires_at);
    if (expires < new Date()) {
      return "bg-red-100 text-red-700";
    }
  }
  return "bg-green-100 text-green-700";
};

const getStatusText = (code) => {
  if (!code.enabled) {
    return "Отозван";
  }
  if (code.used_by) {
    return "Использован";
  }
  if (code.expires_at) {
    const expires = new Date(code.expires_at);
    if (expires < new Date()) {
      return "Истёк";
    }
  }
  return "Активен";
};
</script>
