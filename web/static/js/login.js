// Конфигурация - URL API
const API_URL = window.location.origin;

// Функция для загрузки конфигурации бота
async function loadTelegramConfig() {
    try {
        const response = await fetch(`${API_URL}/api/auth/telegram/config`);
        const config = await response.json();
        initTelegramWidget(config.bot_username);
    } catch (error) {
        console.error('Ошибка загрузки конфигурации:', error);
        showMessage('Ошибка загрузки конфигурации Telegram', 'error');
    }
}

// Инициализация Telegram Widget
function initTelegramWidget(botUsername) {
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', botUsername);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '3');
    script.setAttribute('data-lang', 'ru');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    document.getElementById('telegram-login').appendChild(script);
}

// Колбэк для Telegram Login
async function onTelegramAuth(user) {
    console.log('Telegram user data:', user);

    showMessage('Авторизация...', 'success');

    try {
        const response = await fetch(`${API_URL}/api/auth/telegram`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(user),
            credentials: 'include'
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // Перенаправляем в админку
            window.location.href = '/admin';
        } else {
            showMessage(result.detail || 'Ошибка авторизации', 'error');
            if (response.status === 403) {
                document.getElementById('telegram-login').classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showMessage('Ошибка соединения с сервером', 'error');
    }
}

// Проверка текущей авторизации при загрузке
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/api/auth/me`, {
            credentials: 'include'
        });

        if (response.ok) {
            // Уже авторизован - перенаправляем в админку
            window.location.href = '/admin';
            return;
        }
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
    }
}

// Отображение сообщений
function showMessage(text, type) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');

    if (type === 'success') {
        setTimeout(() => {
            messageEl.classList.add('hidden');
        }, 3000);
    }
}

// Загрузка страницы
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadTelegramConfig();
});
