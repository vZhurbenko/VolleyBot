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

        console.log('checkAuth response status:', response.status);

        if (response.ok) {
            console.log('Пользователь авторизован, добавляем кнопку...');
            
            // Уже авторизован - скрываем виджет и показываем кнопку перехода в админку
            const loginWidget = document.getElementById('telegram-login');
            if (loginWidget) {
                loginWidget.classList.add('hidden');
                console.log('Виджет скрыт');
            }

            // Добавляем кнопку перехода в админку
            const adminBtn = document.createElement('button');
            adminBtn.type = 'button';
            adminBtn.className = 'btn btn-block mt-2';
            adminBtn.textContent = 'Перейти в админ-панель';
            adminBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Клик по кнопке сработал!');
                try {
                    window.location.assign('/admin');
                } catch (err) {
                    console.error('Ошибка редиректа:', err);
                    // Если assign не сработал, пробуем href
                    window.location.href = '/admin';
                }
            });

            const container = document.querySelector('.login-container');
            const messageEl = document.getElementById('message');
            if (messageEl) {
                container.insertBefore(adminBtn, messageEl);
                console.log('Кнопка вставлена перед message');
            } else {
                container.appendChild(adminBtn);
                console.log('Кнопка добавлена в конец container');
            }

            // Проверка видимости кнопки
            setTimeout(() => {
                console.log('Кнопка в DOM:', document.contains(adminBtn));
                console.log('Кнопка видима:', adminBtn.offsetParent !== null);
                console.log('Кнопка styles:', window.getComputedStyle(adminBtn).display);
            }, 100);

            showMessage('Вы уже авторизованы', 'success');
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
