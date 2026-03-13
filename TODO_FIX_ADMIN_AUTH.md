# TODO: Исправить авторизацию админа через /t/{uuid}

## Проблема

Когда администратор (пользователь из `admin_user_ids`) переходит по ссылке `/t/{uuid}`:
1. Его перенаправляет на `/login?redirect=/t/{uuid}`
2. После авторизации через Telegram он попадает в **КАЛЕНДАРЬ** (`/dashboard/calendar`)
3. Вместо того чтобы попасть в **АДМИНКУ** (`/admin`)

## Причина

В `auth_telegram()` проверка `is_admin` работает ПРАВИЛЬНО, но:

1. **Бэкенд** создаёт админа в `users` с `is_admin=True` ✅
2. **НО** фронтенд (LoginView) проверяет `is_guest` и перенаправляет не туда ❌

## Что нужно сделать

### 1. Проверить что возвращает бэкенд

В `app.py` строка ~720:
```python
# 6. Возвращаем данные пользователя (без токенов)
is_guest = db.is_guest(telegram_id)
if is_guest:
    # ...
else:
    user = db.get_user_by_telegram_id(telegram_id)
```

**Проблема:** `db.is_guest()` возвращает `False` для админа → возвращается `user` из `users` ✅

**НО!** В `user` из `users` есть поле `is_admin: True`?

### 2. Проверить LoginView

В `LoginView.vue` после авторизации:
```javascript
if (response.ok && result.success) {
  authStore.setUser(result.user)
  const isGuest = result.user?.is_guest ?? false
  
  if (redirect && trainingRedirectMatch) {
    const uuid = trainingUuid
    if (isGuest) {
      // Гость → страница гостя
      window.location.href = `/guest/training/${uuid}`
    } else {
      // Пользователь → календарь
      window.location.href = `/dashboard/calendar?training=${uuid}`
    }
  }
}
```

**Проблема:** Если `isGuest === false` (админ), то редирект на календарь!

**Нужно:** Проверять `is_admin` и редиректить в админку!

### 3. Исправить LoginView

Добавить проверку `is_admin`:

```javascript
const isAdmin = result.user?.is_admin ?? false

if (redirect && trainingRedirectMatch) {
  const uuid = trainingUuid
  if (isGuest) {
    // Гость → страница гостя
    window.location.href = `/guest/training/${uuid}`
  } else if (isAdmin) {
    // Админ → календарь с модалкой (чтобы мог посмотреть тренировку)
    window.location.href = `/dashboard/calendar?training=${uuid}`
  } else {
    // Обычный пользователь → календарь с модалкой
    window.location.href = `/dashboard/calendar?training=${uuid}`
  }
}
```

### 4. ИЛИ изменить логику

**Вопрос:** Куда должен попадать АДМИН после авторизации через `/t/{uuid}`?

**Варианты:**
1. **В АДМИНКУ** (`/admin`) — чтобы управлять
2. **В КАЛЕНДАРЬ** (`/dashboard/calendar?training={uuid}`) — чтобы записаться на тренировку
3. **НА СТРАНИЦУ ГОСТЯ** (`/guest/training/{uuid}`) — чтобы видеть как гость (но это странно для админа)

**Решение:** Спросить у Владислава!

## Файлы для исправления

1. `web/static/src/views/LoginView.vue` — добавить проверку `is_admin`
2. `web/app.py` — убедиться что `is_admin` возвращается в `user`

## Тесты

После исправления протестировать:

1. **Админ через `/t/{uuid}`** → должен попасть в админку (или календарь?)
2. **Админ через `/`** → должен попасть в админку
3. **Гость через `/t/{uuid}`** → должен попасть на страницу гостя
4. **Гость через `/`** → должен получить 403 (нет доступа)

## Дата

2026-03-13
