# VolleyBot Web Auth

Веб-интерфейс для авторизации администраторов VolleyBot через Telegram Login Widget с управлением настройками бота.

## Структура

```
web/
├── app.py              # FastAPI приложение
├── telegram_auth.py    # Модуль валидации данных Telegram
├── run.py              # Скрипт запуска сервера
├── start_web.sh        # Запуск в фоне (сохраняет PID)
├── stop_web_by_pid.sh  # Остановка сервера
├── .env                # Переменные окружения (не в git)
├── .env.example        # Пример переменных окружения
└── static/
    ├── index.html      # Страница входа
    └── admin.html      # Админ-панель
```

## Установка

1. **Установите зависимости:**
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Настройте переменные окружения:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env при необходимости
   ```

## Запуск

### В режиме разработки:
```bash
python run.py
```

### В фоне (production):
```bash
# Запуск
./start_web.sh

# Проверка статуса
cat web_output.log

# Остановка
./stop_web_by_pid.sh
```

Сервер запустится на `http://localhost:8000`

## Страницы

- **Вход**: `http://localhost:8000/` — страница входа через Telegram
- **Админ-панель**: `http://localhost:8000/admin` — управление настройками

## Безопасность

### Токены
- **Access token**: 30 минут, хранится в HttpOnly cookie
- **Refresh token**: 7 дней, хранится в HttpOnly cookie
- Cookie защищены флагами: `HttpOnly`, `Secure`, `SameSite=lax`

### Авторизация
- Валидация подписи данных Telegram (HMAC-SHA256)
- Проверка времени авторизации (защита от replay атак)
- Проверка администратора через БД
- CSRF защита через SameSite cookie

## Требования к домену

Для работы Telegram Login Widget необходимо:

1. Зарегистрировать домен в @BotFather:
   ```
   /setdomain @VolleyManagerVlg_bot
   ```

2. Указать домен где будет размещён виджет (например: `localhost` для разработки или `volleybot.example.com` для продакшена)

## Разработка

### Тестирование авторизации

1. Откройте `http://localhost:8000`
2. Нажмите кнопку Telegram Login
3. Если ваш Telegram ID есть в администраторах — войдёте в систему

### Проверка списка администраторов

```bash
# Через Python
cd ..
source venv/bin/activate
python -c "from database import Database; db = Database(); print(db.get_admin_ids())"
```

### Добавление администратора

Через бота или напрямую в БД:
```sql
-- Обновить admin_user_ids в таблице settings
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/auth/telegram` | Авторизация через Telegram |
| POST | `/api/auth/refresh` | Обновление access токена |
| GET | `/api/auth/me` | Получить данные текущего пользователя |
| POST | `/api/auth/logout` | Выход из системы |
| GET | `/api/auth/telegram/config` | Конфигурация для виджета |
| GET | `/api/admin/users` | Список всех пользователей (только админ) |
| GET | `/health` | Проверка здоровья API |

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather | - |
| `TELEGRAM_BOT_USERNAME` | Имя бота (без @) | - |
| `JWT_SECRET` | Секретный ключ для JWT | `volleybot_jwt_secret_key_change_in_prod` |
| `HOST` | Хост для сервера | `0.0.0.0` |
| `PORT` | Порт для сервера | `8000` |
| `VOLLEYBOT_DB_PATH` | Путь к базе данных | `../volleybot.db` |
