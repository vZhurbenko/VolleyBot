"""
FastAPI приложение для авторизации через Telegram Login Widget
с проверкой администратора через БД VolleyBot

Использует access + refresh токены в HttpOnly cookie
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, List

# Добавляем родительскую директорию в path для импорта database
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import jwt
import logging

from database import Database
from telegram_auth import TelegramAuth

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация приложения
app = FastAPI(title="VolleyBot Auth API")

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://volleybot.zhurbenko.dev"],  # Только наш домен
    allow_credentials=True,  # Разрешить cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or Path(__file__).parent.parent.joinpath(".bot_token").read_text().strip()
JWT_SECRET = os.getenv("JWT_SECRET", "volleybot_jwt_secret_key_change_in_prod")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Access token живёт 30 минут
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Refresh token живёт 7 дней
DB_PATH = os.getenv("VOLLEYBOT_DB_PATH", str(Path(__file__).parent.parent / "volleybot.db"))

# Инициализация
telegram_auth = TelegramAuth(BOT_TOKEN)
db = Database(DB_PATH)
db.create_tables()  # Создаём таблицы если не существуют
security = HTTPBearer(auto_error=False)


# ==================== Pydantic модели ====================

class TelegramUserData(BaseModel):
    """Модель данных пользователя от Telegram"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class AuthResponse(BaseModel):
    """Модель ответа авторизации"""
    success: bool
    message: str
    user: Optional[dict] = None


class UserInfo(BaseModel):
    """Модель информации о пользователе"""
    id: int
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    is_admin: bool
    last_login: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    """Модель запроса на обновление токена"""
    pass


# ==================== Вспомогательные функции ====================

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    """Создание access токена"""
    import uuid
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4())  # Уникальный ID токена (соль)
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta) -> str:
    """Создание refresh токена"""
    import uuid
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())  # Уникальный ID токена (соль)
    })
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict:
    """Декодирование и проверка токена"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный тип токена",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истёк",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
        )


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> Response:
    """Установка HttpOnly cookie с токенами"""
    # Access token - 30 минут
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,      # JavaScript не имеет доступа
        secure=True,        # Только HTTPS
        samesite="lax",     # Защита от CSRF
        path="/api"         # Только для API endpoints
    )
    
    # Refresh token - 7 дней
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api"
    )
    
    return response


def clear_auth_cookies(response: Response) -> Response:
    """Удаление cookie с токенами"""
    response.delete_cookie(key="access_token", path="/api")
    response.delete_cookie(key="refresh_token", path="/api")
    return response


async def get_current_user_from_access_cookie(request: Request) -> dict:
    """Получение текущего пользователя из access token cookie"""
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token не найден",
        )
    
    payload = decode_token(access_token, "access")
    telegram_id = payload.get("sub")
    
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
        )
    
    # Получаем пользователя из БД
    user = db.get_user_by_telegram_id(int(telegram_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    
    return user


def require_auth(user: dict) -> dict:
    """Проверка что пользователь авторизован"""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )
    return user


def require_admin(user: dict) -> dict:
    """Проверка что пользователь является администратором"""
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется права администратора",
        )
    return user


# ==================== API эндпоинты ====================

@app.post("/api/auth/telegram")
async def auth_telegram(user_data: TelegramUserData, response: Response):
    """
    Эндпоинт для авторизации через Telegram Login Widget
    Устанавливает access и refresh токены в HttpOnly cookie
    """
    logger.info(f"Попытка авторизации пользователя: {user_data.username or user_data.first_name}")

    # 1. Проверяем валидность hash
    if not telegram_auth.validate(user_data.dict()):
        logger.warning(f"Неверная подпись данных для пользователя {user_data.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная подпись данных"
        )

    # 2. Проверяем время авторизации (защита от replay атак)
    if not telegram_auth.is_auth_date_valid(user_data.auth_date, max_age_seconds=300):
        logger.warning(f"Данные авторизации устарели для пользователя {user_data.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Данные авторизации устарели"
        )

    telegram_id = user_data.id

    # 3. Проверяем является ли пользователь администратором
    admin_ids = db.get_admin_ids()
    is_admin = telegram_id in admin_ids

    if not is_admin:
        logger.warning(f"Пользователь {telegram_id} не является администратором")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только администраторы могут войти"
        )

    # 4. Сохраняем или обновляем пользователя в БД
    existing_user = db.get_user_by_telegram_id(telegram_id)

    if not existing_user:
        db.add_user(
            telegram_id=telegram_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            photo_url=user_data.photo_url,
            is_admin=is_admin
        )
        logger.info(f"Новый администратор зарегистрирован: {user_data.username or user_data.first_name}")
    else:
        db.update_user(
            telegram_id=telegram_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            photo_url=user_data.photo_url
        )
        logger.info(f"Администратор обновил данные: {user_data.username or user_data.first_name}")

    # 5. Создаём токены
    token_data = {
        "sub": str(telegram_id),
        "username": user_data.username,
        "is_admin": is_admin
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    # 6. Устанавливаем cookie
    set_auth_cookies(response, access_token, refresh_token)

    # 7. Возвращаем данные пользователя (без токенов)
    user = db.get_user_by_telegram_id(telegram_id)
    return {
        "success": True,
        "message": "Авторизация успешна",
        "user": user
    }


@app.post("/api/auth/refresh")
async def refresh_access_token(request: Request, response: Response):
    """
    Обновление access токена используя refresh token
    """
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token не найден",
        )
    
    # Проверяем refresh token
    payload = decode_token(refresh_token, "refresh")
    telegram_id = payload.get("sub")
    
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный refresh token",
        )
    
    # Проверяем что пользователь всё ещё админ
    user = db.get_user_by_telegram_id(int(telegram_id))
    if not user or not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь больше не является администратором",
        )
    
    # Создаём новый access token
    token_data = {
        "sub": str(telegram_id),
        "username": user.get("username"),
        "is_admin": True
    }
    
    new_access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Устанавливаем новый access token (refresh оставляем тот же)
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api"
    )
    
    return {"success": True, "message": "Токен обновлён"}


@app.get("/api/auth/me")
async def get_current_user_info(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение данных текущего пользователя
    """
    return user


@app.post("/api/auth/logout")
async def logout(response: Response):
    """
    Выход из системы (удаление cookie)
    """
    clear_auth_cookies(response)
    return {"success": True, "message": "Выход выполнен"}


@app.get("/api/auth/telegram/config")
async def get_telegram_config():
    """
    Эндпоинт для получения конфигурации Telegram виджета
    """
    bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "VolleyManagerVlg_bot")
    return {
        "bot_username": bot_username,
        "button_size": "large",
        "lang": "ru"
    }


@app.get("/api/admin/users", response_model=List[UserInfo])
async def get_all_users(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение списка всех пользователей (только для администраторов)
    """
    require_admin(user)
    users = db.get_all_users()
    return users


# ==================== API для управления ботом ====================

class PollTemplate(BaseModel):
    """Модель шаблона опроса"""
    name: str
    description: str
    training_day: str
    poll_day: str
    training_time: str
    options: List[str]
    enabled: bool = True
    default_chat_id: str = ""
    default_topic_id: Optional[int] = None


class PollSchedule(BaseModel):
    """Модель расписания опроса"""
    name: str
    chat_id: str
    message_thread_id: Optional[int] = None
    training_day: str
    poll_day: str
    training_time: str
    enabled: bool = True


@app.get("/api/admin/settings/template")
async def get_poll_template(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение шаблона опроса по умолчанию
    """
    require_admin(user)
    template = db.get_default_template()
    return template


@app.put("/api/admin/settings/template")
async def update_poll_template(template: PollTemplate, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Обновление шаблона опроса по умолчанию
    """
    require_admin(user)
    db.set_default_template(template.dict())
    return {"success": True, "message": "Шаблон обновлён"}


@app.get("/api/admin/settings/schedules")
async def get_poll_schedules(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение всех расписаний опросов
    """
    require_admin(user)
    schedules = db.get_poll_schedules()
    return schedules


@app.post("/api/admin/settings/schedules")
async def add_poll_schedule(schedule: PollSchedule, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Добавление нового расписания опроса
    """
    require_admin(user)
    schedule_dict = schedule.dict()
    schedule_dict['id'] = str(uuid.uuid4())
    db.add_poll_schedule(schedule_dict)
    return {"success": True, "message": "Расписание добавлено", "id": schedule_dict['id']}


@app.put("/api/admin/settings/schedules/{schedule_id}")
async def update_poll_schedule(schedule_id: str, updates: dict, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Обновление расписания опроса
    """
    require_admin(user)
    db.update_poll_schedule(schedule_id, updates)
    return {"success": True, "message": "Расписание обновлено"}


@app.delete("/api/admin/settings/schedules/{schedule_id}")
async def remove_poll_schedule(schedule_id: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Удаление расписания опроса
    """
    require_admin(user)
    db.remove_poll_schedule(schedule_id)
    return {"success": True, "message": "Расписание удалено"}


@app.get("/api/admin/settings/active_polls")
async def get_active_polls(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение всех активных опросов
    """
    require_admin(user)
    polls = db.get_active_polls()
    return polls


@app.get("/api/admin/settings/admin_ids")
async def get_admin_ids(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение списка ID администраторов
    """
    require_admin(user)
    admin_ids = db.get_admin_ids()
    return {"admin_ids": admin_ids}


@app.post("/api/admin/settings/admin_ids")
async def add_admin_id(request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Добавление ID администратора
    """
    require_admin(user)
    body = await request.json()
    admin_id = body.get('admin_id')
    if not admin_id:
        raise HTTPException(status_code=400, detail="admin_id required")
    db.add_admin_id(int(admin_id))
    
    # Обновляем поле is_admin в таблице users
    db.update_user_admin_status(int(admin_id), True)
    
    return {"success": True, "message": "Администратор добавлен"}


@app.delete("/api/admin/settings/admin_ids/{admin_id}")
async def remove_admin_id(admin_id: int, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Удаление ID администратора
    """
    require_admin(user)
    admin_ids = db.get_admin_ids()
    if admin_id in admin_ids:
        admin_ids.remove(admin_id)
        db.set_admin_ids(admin_ids)
    
    # Обновляем поле is_admin в таблице users
    db.update_user_admin_status(int(admin_id), False)
    
    return {"success": True, "message": "Администратор удалён"}



# ==================== API для пользователей (Calendar) ====================

@app.get("/api/user/calendar")
async def get_calendar(year: int, month: int, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение календаря тренировок на месяц
    Возвращает все тренировки месяца с записями
    """
    from datetime import datetime, timedelta
    import calendar
    
    # Получаем все расписания
    schedules = db.get_poll_schedules()
    
    # Получаем разовые тренировки на месяц
    one_time_trainings = db.get_one_time_trainings(year, month)
    
    # Генерируем все даты тренировок на месяц
    trainings = {}
    
    # Дни недели для mapping
    day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
               'friday': 4, 'saturday': 5, 'sunday': 6}
    
    # Для каждого расписания генерируем даты
    for schedule in schedules:
        if not schedule.get('enabled', True):
            continue
            
        training_day = schedule.get('training_day', 'monday')
        training_time = schedule.get('training_time', '')
        chat_id = schedule.get('chat_id', '')
        topic_id = schedule.get('message_thread_id')
        
        weekday = day_map.get(training_day.lower(), 0)
        
        # Находим все дни этого weekday в месяце
        cal = calendar.monthcalendar(year, month)
        for week in cal:
            day = week[weekday]
            if day == 0:
                continue
            
            date_str = f"{year}-{month:02d}-{day:02d}"
            key = f"{date_str}_{training_time}_{chat_id}"
            
            if key not in trainings:
                trainings[key] = {
                    'date': date_str,
                    'time': training_time,
                    'chat_id': chat_id,
                    'topic_id': topic_id,
                    'is_one_time': False,
                    'registrations': []
                }
    
    # Добавляем разовые тренировки
    for training in one_time_trainings:
        date_str = training.get('training_date', '')
        time = training.get('training_time', '')
        chat_id = training.get('chat_id', '')
        topic_id = training.get('topic_id')
        name = training.get('name', '')
        
        key = f"{date_str}_{time}_{chat_id}"
        if key not in trainings:
            trainings[key] = {
                'date': date_str,
                'time': time,
                'chat_id': chat_id,
                'topic_id': topic_id,
                'is_one_time': True,
                'name': name,
                'registrations': []
            }
    
    # Для каждой тренировки получаем записи
    for key, training in trainings.items():
        registrations = db.get_training_registrations(
            training['date'], training['time'], training['chat_id']
        )
        training['registrations'] = registrations
        training['registered_count'] = len([r for r in registrations if r.get('status') == 'registered'])
        training['waitlist_count'] = len([r for r in registrations if r.get('status') == 'waitlist'])
        
        # Проверяем записан ли текущий пользователь
        user_telegram_id = user.get('telegram_id')
        user_registration = next((r for r in registrations if r.get('user_telegram_id') == user_telegram_id), None)
        training['user_status'] = user_registration['status'] if user_registration else None
    
    return {"trainings": list(trainings.values())}


@app.post("/api/user/calendar/register")
async def register_for_training(request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Запись на тренировку
    """
    require_auth(user)
    
    body = await request.json()
    training_date = body.get('training_date')
    training_time = body.get('training_time')
    chat_id = body.get('chat_id')
    topic_id = body.get('topic_id')
    
    if not all([training_date, training_time, chat_id]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    user_telegram_id = user.get('telegram_id')
    training_id = f"{training_date}_{training_time}_{chat_id}"
    
    result = db.register_for_training(
        training_id, training_date, training_time, chat_id, topic_id, user_telegram_id
    )
    
    if result.get('success'):
        return {"success": True, "status": result.get('status')}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Registration failed'))


@app.post("/api/user/calendar/unregister")
async def unregister_from_training(request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Отписка от тренировки
    """
    require_auth(user)
    
    body = await request.json()
    training_date = body.get('training_date')
    training_time = body.get('training_time')
    chat_id = body.get('chat_id')
    
    if not all([training_date, training_time, chat_id]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    user_telegram_id = user.get('telegram_id')
    
    result = db.unregister_from_training(training_date, training_time, chat_id, user_telegram_id)
    
    if result.get('success'):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Unregistration failed'))


@app.get("/api/user/my-trainings")
async def get_my_trainings(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение моих записей на тренировки
    """
    require_auth(user)
    
    user_telegram_id = user.get('telegram_id')
    trainings = db.get_user_trainings(user_telegram_id)
    
    return {"trainings": trainings}


# ==================== API для админов (Users & Trainings) ====================

@app.get("/api/admin/users")
async def get_users(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение списка всех пользователей (только админы)
    """
    require_admin(user)
    users = db.get_all_web_users()
    logger.info(f"get_all_web_users returned {len(users)} users")
    if users:
        logger.info(f"First user keys: {list(users[0].keys())}")
    return {"users": users}


@app.post("/api/admin/users")
async def add_user(request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Добавление пользователя по Telegram ID (только админы)
    """
    require_admin(user)
    
    body = await request.json()
    telegram_id = body.get('telegram_id')
    
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id required")
    
    result = db.add_web_user_by_telegram_id(int(telegram_id))
    
    if result.get('success'):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to add user'))


@app.delete("/api/admin/users/{telegram_id}")
async def remove_user(telegram_id: int, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Удаление пользователя (только админы)
    """
    require_admin(user)

    result = db.remove_web_user(telegram_id)

    if result.get('success'):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to remove user'))


@app.post("/api/admin/users/{telegram_id}/toggle-active")
async def toggle_user_active(
    telegram_id: int,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Переключение статуса активности пользователя (только админы)
    """
    require_admin(user)
    
    # Получаем текущий статус
    user_data = db.get_user_by_telegram_id(telegram_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    new_status = not user_data.get('is_active', True)
    result = db.toggle_user_active_status(telegram_id, new_status)
    
    if result.get('success'):
        return {"success": True, "message": f"Пользователь {'активирован' if new_status else 'деактивирован'}"}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to toggle status'))


@app.post("/api/admin/calendar/add-training")
async def add_one_time_training(request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Добавление разовой тренировки (только админы)
    """
    require_admin(user)
    
    body = await request.json()
    training_date = body.get('training_date')
    training_time = body.get('training_time')
    chat_id = body.get('chat_id')
    topic_id = body.get('topic_id')
    name = body.get('name', 'Тренировка')
    
    if not all([training_date, training_time, chat_id]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    training_id = f"{training_date}_{training_time}_{chat_id}"
    
    result = db.add_one_time_training(training_id, training_date, training_time, chat_id, topic_id, name)
    
    if result.get('success'):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to add training'))


@app.delete("/api/admin/calendar/remove-training/{training_id}")
async def remove_one_time_training(training_id: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Удаление разовой тренировки (только админы)
    """
    require_admin(user)
    
    result = db.remove_one_time_training(training_id)
    
    if result.get('success'):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to remove training'))


@app.get("/api/admin/trainings")
async def get_all_trainings(start_date: str, end_date: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение всех записей на тренировки за период (только админы)
    """
    require_admin(user)
    
    trainings = db.get_all_trainings(start_date, end_date)
    return {"trainings": trainings}


# ==================== API для приглашений ====================

class InviteCodeCreate(BaseModel):
    """Модель создания кода приглашения"""
    expires_in_days: Optional[int] = None  # 1, 7, 30, None (бессрочно)


@app.post("/api/admin/invite")
async def create_invite_code(
    request: InviteCodeCreate,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Создание кода приглашения (только админы)
    """
    require_admin(user)

    import uuid
    from datetime import datetime, timedelta

    code = str(uuid.uuid4())[:8]  # Короткий код из 8 символов
    created_by = user.get('telegram_id')

    # Вычисляем срок действия
    expires_at = None
    if request.expires_in_days:
        expires_at = (datetime.now() + timedelta(days=request.expires_in_days)).isoformat()

    result = db.create_invite_code(code, created_by, expires_at)

    if result.get('success'):
        return {
            "success": True,
            "code": code,
            "expires_at": expires_at,
            "url": f"/invite/{code}"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to create invite code'))


@app.get("/api/admin/invite")
async def get_invite_codes(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение всех кодов приглашений (только админы)
    """
    require_admin(user)

    codes = db.get_all_invite_codes()
    return {"codes": codes}


@app.delete("/api/admin/invite/{code}")
async def deactivate_invite_code(
    code: str,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Отзыв кода приглашения (только админы)
    """
    require_admin(user)

    result = db.deactivate_invite_code(code)

    if result:
        return {"success": True, "message": "Код отозван"}
    else:
        raise HTTPException(status_code=404, detail="Код не найден")


@app.get("/api/invite/{code}")
async def get_invite_code_info(code: str):
    """
    Проверка кода приглашения (публичный эндпоинт)
    """
    invite = db.get_invite_code(code)

    if not invite:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")

    # Проверяем, не истёк ли срок
    if invite.get('expires_at'):
        from datetime import datetime
        expires_at = datetime.fromisoformat(invite['expires_at'])
        if expires_at < datetime.now():
            raise HTTPException(status_code=410, detail="Срок действия приглашения истёк")

    # Проверяем, не использован ли
    if invite.get('used_by'):
        raise HTTPException(status_code=410, detail="Приглашение уже использовано")

    # Проверяем, активен ли
    if not invite.get('enabled'):
        raise HTTPException(status_code=410, detail="Приглашение отозвано")

    return {
        "success": True,
        "code": code,
        "expires_at": invite.get('expires_at')
    }


@app.post("/api/invite/{code}/accept")
async def accept_invite_code(
    code: str,
    request: Request,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Использование кода приглашения
    """
    require_auth(user)

    # Проверяем код
    invite = db.get_invite_code(code)

    if not invite:
        raise HTTPException(status_code=404, detail="Приглашение не найдено")

    # Проверяем, не истёк ли срок
    if invite.get('expires_at'):
        from datetime import datetime
        expires_at = datetime.fromisoformat(invite['expires_at'])
        if expires_at < datetime.now():
            raise HTTPException(status_code=410, detail="Срок действия приглашения истёк")

    # Проверяем, не использован ли
    if invite.get('used_by'):
        raise HTTPException(status_code=410, detail="Приглашение уже использовано")

    # Проверяем, активен ли
    if not invite.get('enabled'):
        raise HTTPException(status_code=410, detail="Приглашение отозвано")

    # Используем код
    telegram_id = user.get('telegram_id')
    result = db.use_invite_code(code, telegram_id)

    if result:
        return {"success": True, "message": "Вы успешно присоединились!"}
    else:
        raise HTTPException(status_code=500, detail="Не удалось использовать приглашение")


# ==================== Статика ====================

static_path = Path(__file__).parent / "static" / "dist"
assets_path = static_path / "assets"

# Монтируем директорию ассетов для CSS/JS файлов
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

# Монтируем dist для favicon и других файлов
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path, html=True), name="static")


@app.get("/health")
async def health_check():
    """
    Проверка здоровья API
    """
    return {
        "status": "ok",
        "database": "connected" if db.conn else "disconnected"
    }


@app.get("/{full_path:path}")
async def root(full_path: str):
    """
    Главная страница и все роуты - отдаём Vue.js приложение
    """
    # Если это API запрос или ассеты - пропускаем
    if full_path.startswith('api/') or full_path.startswith('static/') or full_path.startswith('assets/'):
        raise HTTPException(status_code=404)

    # Иначе отдаём index.html для Vue Router
    index_path = Path(__file__).parent / "static" / "dist" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "VolleyBot Auth API - build not found"}
