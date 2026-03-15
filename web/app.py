"""
FastAPI приложение для авторизации через Telegram Login Widget
с проверкой администратора через БД VolleyBot

Использует access + refresh токены в HttpOnly cookie
"""

import os
import sys
import uuid
import json
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
from pydantic import BaseModel, Field, validator
import jwt
import logging

from database import Database
from telegram_auth import TelegramAuth

# APScheduler для автоматического создания тренировок и опросов
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("DEBUG: app.py загружен!", file=sys.stderr, flush=True)

# Инициализация приложения
app = FastAPI(title="VolleyBot Auth API")

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://volleyteam.ru", "https://www.volleyteam.ru"],  # Только наш домен
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

# Инициализация планировщика
scheduler = AsyncIOScheduler()


# ==================== Middleware для ограничения доступа гостей ====================

@app.middleware("http")
async def guest_access_middleware(request: Request, call_next):
    """
    Middleware для ограничения доступа гостей
    
    Гости могут accessing только:
    - /api/guest/*
    - /api/trainings/{uuid} (только своя тренировка)
    
    Заблокировать доступ к:
    - /api/users/*
    - /api/trainings (список всех тренировок)
    - /api/calendar/*
    - /api/profile/*
    """
    # Пропускаем без проверки
    if request.url.path in ["/health", "/api/auth/telegram", "/api/auth/refresh", "/api/invite/"]:
        return await call_next(request)

    # Получаем пользователя из токена
    user = get_current_user_from_access_token(request)

    # Если пользователь не авторизован - пропускаем (авторизация проверится в endpoint)
    if not user:
        return await call_next(request)
    
    # Проверяем, является ли пользователь гостем
    is_guest = user.get('is_guest', False)

    if is_guest:
        path = request.url.path

        # Разрешённые пути для гостей
        allowed_paths = [
            '/api/guest/me',
            '/api/guest/auth',
            '/api/guest/join/',
            '/api/guest/leave/',
        ]

        # Проверяем точное совпадение или начало пути
        is_allowed = any(
            path == allowed or path.startswith(allowed)
            for allowed in allowed_paths
        )
        
        # Разрешаем гостям доступ к странице гостя /guest/training/{uuid}
        if path.startswith('/guest/training/'):
            is_allowed = True
        
        # Разрешаем гостям доступ к конкретной тренировке по UUID
        if path.startswith('/api/trainings/'):
            is_allowed = True
        
        # Разрешаем гостям доступ к календарю с параметром training
        if path == '/api/user/calendar':
            from urllib.parse import parse_qs
            query_string = request.url.query
            query_params = parse_qs(query_string)
            if 'training' in query_params:
                is_allowed = True

        # Блокируем доступ к админским и пользовательским endpoint'ам
        blocked_prefixes = [
            '/api/admin/',
            '/api/users/',
            '/api/profile/',
        ]

        is_blocked = any(path.startswith(prefix) for prefix in blocked_prefixes)

        # Блокируем получение списка всех тренировок
        if path == '/api/trainings':
            is_blocked = True
        
        if is_blocked:
            logger.warning(f"Гость {user.get('telegram_id')} попытался получить доступ к {path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Доступ запрещён. У вас нет прав для просмотра этого раздела."}
            )
    
    return await call_next(request)


# ==================== Планировщик задач ====================

async def add_trainings_and_polls_from_schedules():
    """
    Автоматическое добавление тренировок из расписаний в календарь за 3 дня
    и вызов API бота для создания опросов
    Запускается каждый день в 12:00
    """
    logger.info("Запуск автоматического добавления тренировок и опросов из расписаний")

    from datetime import datetime, timedelta
    import uuid as uuid_module
    import httpx

    # Получаем все активные расписания
    schedules = db.get_poll_schedules()

    # Дата через 3 дня (тренировки которые нужно добавить)
    target_date = datetime.now() + timedelta(days=3)
    target_date_str = target_date.strftime('%Y-%m-%d')

    # Дни недели для mapping
    day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
               'friday': 4, 'saturday': 5, 'sunday': 6}

    target_weekday = target_date.weekday()

    added_count = 0
    poll_count = 0

    # API ключ для вызова бота
    bot_api_key = os.getenv('BOT_API_KEY', 'volleybot_secret_key')
    bot_api_url = 'http://127.0.0.1:8001/api/create_poll'

    for schedule in schedules:
        if not schedule.get('enabled', True):
            continue

        # Проверяем, совпадает ли день недели расписания с целевым днём
        training_day = schedule.get('training_day', 'monday')
        schedule_weekday = day_map.get(training_day.lower(), -1)

        if schedule_weekday != target_weekday:
            continue

        # Проверяем, есть ли уже такая тренировка в календаре
        existing = db.get_scheduled_training_by_schedule_and_date(
            schedule['id'], target_date_str
        )

        if existing:
            logger.info(f"Тренировка из расписания {schedule['id']} на {target_date_str} уже существует")
            continue

        # Генерируем уникальный ID для тренировки
        training_id = f"sched_{schedule['id']}_{target_date_str}_{str(uuid_module.uuid4())[:8]}"

        # Получаем параметры тренировки
        start_time = schedule.get('start_time', '')
        end_time = schedule.get('end_time', '')
        training_time = f"{start_time} - {end_time}"
        chat_id = schedule.get('chat_id', '')
        topic_id = schedule.get('message_thread_id')
        name = schedule.get('name', 'Тренировка')
        location = schedule.get('location', '')

        # Добавляем тренировку в календарь
        result = db.add_scheduled_training(
            training_id=training_id,
            schedule_id=schedule['id'],
            training_date=target_date_str,
            training_time=training_time,
            chat_id=chat_id,
            topic_id=topic_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            location=location
        )

        if result.get('success'):
            logger.info(f"Добавлена тренировка из расписания {schedule['id']} на {target_date_str}")
            added_count += 1

            # Вызываем API бота для создания опроса
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        bot_api_url,
                        json={
                            'chat_id': chat_id,
                            'topic_id': topic_id,
                            'training_date': target_date_str,
                            'start_time': start_time,
                            'end_time': end_time,
                            'location': location,
                            'name': name
                        },
                        headers={'X-API-Key': bot_api_key},
                        timeout=30
                    )
                    api_result = response.json()

                    if response.status_code == 200 and api_result.get('success'):
                        poll_count += 1
                        logger.info(f"Создан опрос для тренировки {schedule['id']} в Telegram")
                    else:
                        logger.error(f"Ошибка API бота: {api_result}")
            except Exception as e:
                logger.error(f"Ошибка вызова API бота: {e}")
        else:
            logger.error(f"Ошибка добавления тренировки из расписания {schedule['id']}: {result.get('error')}")

    logger.info(f"Добавлено {added_count} тренировок, создано {poll_count} опросов на {target_date_str}")

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
    invite_code: Optional[str] = None
    training_uuid: Optional[str] = None  # UUID тренировки для гостей


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
    is_active: bool
    is_guest: bool = False
    last_login: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    """Модель запроса на обновление токена"""
    pass


class GuestAuthRequest(BaseModel):
    """Модель запроса авторизации гостя"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
    training_uuid: Optional[str] = None


class GuestResponse(BaseModel):
    """Модель ответа информации о госте"""
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    training_uuid: str
    is_active: bool
    is_guest: bool


class GuestStatusUpdate(BaseModel):
    """Модель обновления статуса гостя"""
    is_active: bool


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


def get_current_user_from_access_token(request: Request) -> Optional[dict]:
    """
    Получение текущего пользователя из access token cookie
    Возвращает None если токен не валиден (для опциональной авторизации)
    """
    access_token = request.cookies.get("access_token")

    if not access_token:
        return None

    try:
        payload = decode_token(access_token, "access")
        telegram_id = payload.get("sub")

        if not telegram_id:
            return None

        user = db.get_user_by_telegram_id(int(telegram_id))
        return user
    except HTTPException:
        return None


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
        path="/"            # Доступно на всех страницах
    )

    # Refresh token - 7 дней
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=True,        # Только HTTPS
        samesite="lax",
        path="/"            # Доступно на всех страницах
    )

    return response


def clear_auth_cookies(response: Response) -> Response:
    """Удаление cookie с токенами"""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    # Проверяем, что пользователь активен
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
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
    # Сохраняем invite_code до валидации
    invite_code = user_data.invite_code
    
    logger.info(f"Попытка авторизации пользователя: {user_data.username or user_data.first_name}")
    logger.info(f"invite_code: {invite_code}")

    # 1. Проверяем валидность hash (invite_code не должен участвовать в валидации)
    # Временно удаляем invite_code из данных для валидации
    user_data_for_validation = user_data.model_copy()
    user_data_for_validation.invite_code = None
    
    if not telegram_auth.validate(user_data_for_validation.dict(exclude_none=True)):
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

    # 3. Проверяем, существует ли пользователь в БД
    existing_user = db.get_user_by_telegram_id(telegram_id)

    # Если пользователя нет в БД — проверяем, есть ли приглашение, training_uuid
    if not existing_user:
        invite_code = user_data.invite_code
        training_uuid = user_data.training_uuid
        invite_valid = False

        # Новый пользователь без приглашения и training_uuid — запрещаем вход
        logger.info(f"Пользователь {telegram_id} не найден в БД, проверяем приглашение/training_uuid")

        # Проверяем приглашение
        if invite_code:
            invite = db.get_invite_code(invite_code)
            if invite and invite.get('enabled') and not invite.get('used_by'):
                from datetime import datetime
                if not invite.get('expires_at') or datetime.fromisoformat(invite['expires_at']) > datetime.now():
                    invite_valid = True
                    logger.info(f"Валидное приглашение {invite_code} для пользователя {telegram_id}")

        # Если нет валидного приглашения — проверяем training_uuid (гость)
        if not invite_valid and training_uuid:
            # Проверяем валидность тренировки
            training = db.get_training_by_uuid(training_uuid)
            if training:
                invite_valid = True
                logger.info(f"Валидная тренировка {training_uuid} для пользователя {telegram_id}")

        # Если нет валидного приглашения или training_uuid — запрещаем вход
        if not invite_valid:
            logger.warning(f"Пользователь {telegram_id} не найден в БД, не имеет приглашения или training_uuid")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вам недоступна авторизация. Обратитесь к администратору."
            )

        # Создаём пользователя (гостя или с приглашением)
        if training_uuid:
            # Создаём гостя для записи на тренировку
            db.add_guest(
                telegram_id=telegram_id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username,
                photo_url=user_data.photo_url
            )
            logger.info(f"Гость создан: {user_data.username or user_data.first_name}")

            # Записываем на тренировку
            db.add_guest_signup(
                telegram_id=telegram_id,
                training_uuid=training_uuid,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username,
                photo_url=user_data.photo_url
            )
            logger.info(f"Гость записан на тренировку {training_uuid}")

            # Получаем обновлённый список тренировок
            trainings = db.get_guest_trainings(telegram_id)
            training_uuids = [t['training_uuid'] for t in trainings]

            existing_user = {
                'telegram_id': telegram_id,
                'first_name': user_data.first_name,
                'last_name': user_data.last_name,
                'username': user_data.username,
                'photo_url': user_data.photo_url,
                'is_guest': True,
                'trainings': training_uuids
            }
        elif invite_valid:
            # Создаём пользователя с приглашением
            db.add_user(
                telegram_id=telegram_id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username,
                photo_url=user_data.photo_url,
                is_admin=False
            )
            logger.info(f"Пользователь зарегистрирован по приглашению: {user_data.username or user_data.first_name}")
            existing_user = db.get_user_by_telegram_id(telegram_id)

            if invite_code:
                db.use_invite_code(invite_code, telegram_id)
                logger.info(f"Пользователь {telegram_id} принял приглашение {invite_code}")
    else:
        # Проверяем, активен ли пользователь
        if not existing_user.get('is_active', True):
            logger.warning(f"Пользователь {telegram_id} деактивирован")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ваш аккаунт деактивирован"
            )

        # Обновляем данные пользователя из Telegram (аватар, имя, username)
        db.update_user(
            telegram_id=telegram_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            photo_url=user_data.photo_url
        )
        logger.info(f"Пользователь обновил данные: {user_data.username or user_data.first_name}")

        # НЕ обновляем статус админа автоматически из настроек
        # Статус админа управляется только через явное добавление/удаление админа
        # existing_user уже содержит актуальный is_admin из БД

    # 4. Создаём токены
    is_admin = existing_user.get('is_admin', False)
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

    # 5. Устанавливаем cookie
    set_auth_cookies(response, access_token, refresh_token)

    # 6. Возвращаем данные пользователя (без токенов)
    user = db.get_user_by_telegram_id(telegram_id)

    # Добавляем список тренировок для гостя
    if user and user.get('is_guest'):
        trainings = db.get_guest_trainings(telegram_id)
        training_uuids = [t['training_uuid'] for t in trainings] if trainings else []
        user['trainings'] = training_uuids

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
    # Добавляем is_guest в ответ
    user['is_guest'] = user.get('is_guest', False)
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


# ==================== API для гостей ====================

@app.post("/api/guest/auth")
async def guest_auth(user_data: GuestAuthRequest, response: Response):
    """
    Авторизация гостя через Telegram

    Логика:
    - Если пользователь есть в users → вернуть токен с is_guest: false
    - Если есть в guests → вернуть токен с is_guest: true и списком тренировок
    - Если нет нигде → проверить training_uuid:
      - Если есть → добавить в guests и guest_signups, вернуть токен
      - Если нет → ошибка
    """
    logger.info(f"Попытка авторизации гостя: {user_data.username or user_data.first_name}")

    # 1. Проверяем валидность hash
    if not telegram_auth.validate(user_data.dict(exclude={'training_uuid'}, exclude_none=True)):
        logger.warning(f"Неверная подпись данных для гостя {user_data.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверная подпись данных"
        )

    # 2. Проверяем время авторизации
    if not telegram_auth.is_auth_date_valid(user_data.auth_date, max_age_seconds=300):
        logger.warning(f"Данные авторизации устарели для гостя {user_data.id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Данные авторизации устарели"
        )

    telegram_id = user_data.id
    training_uuid = user_data.training_uuid

    # 3. Проверяем, существует ли пользователь в users
    existing_user = db.get_user_by_telegram_id(telegram_id)

    if existing_user:
        # Пользователь существует в users - возвращаем токен как обычный пользователь
        logger.info(f"Гость {telegram_id} найден как пользователь")

        # Проверяем активен ли пользователь
        if not existing_user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ваш аккаунт деактивирован"
            )

        # Обновляем данные пользователя
        db.update_user(
            telegram_id=telegram_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            username=user_data.username,
            photo_url=user_data.photo_url
        )

        # Создаём токены
        token_data = {
            "sub": str(telegram_id),
            "username": user_data.username,
            "is_admin": existing_user.get('is_admin', False),
            "is_guest": False
        }

        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        set_auth_cookies(response, access_token, refresh_token)

        return {
            "success": True,
            "message": "Авторизация успешна",
            "user": existing_user,
            "is_guest": False,
            "trainings": []
        }

    # 4. Проверяем, существует ли пользователь в guests
    existing_guest = db.get_guest_by_telegram(telegram_id)

    if existing_guest:
        # Гость существует - проверяем активен ли
        if not existing_guest.get('is_active', True):
            logger.warning(f"Гость {telegram_id} деактивирован")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Ваш аккаунт гостя деактивирован"
            )

        # Обновляем данные гостя
        cursor = db.conn.cursor()
        cursor.execute('''
            UPDATE guests
            SET first_name = ?, last_name = ?, username = ?, photo_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
        ''', (user_data.first_name, user_data.last_name, user_data.username, user_data.photo_url, telegram_id))
        db.conn.commit()

        # Получаем обновлённые данные
        guest = db.get_guest_by_telegram(telegram_id)

        # Получаем список тренировок гостя
        trainings = db.get_guest_trainings(telegram_id)

        # Создаём токены
        token_data = {
            "sub": str(telegram_id),
            "username": user_data.username,
            "is_guest": True
        }

        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        set_auth_cookies(response, access_token, refresh_token)

        logger.info(f"Гость {telegram_id} авторизован, тренировок: {len(trainings)}")
        return {
            "success": True,
            "message": "Авторизация успешна",
            "user": guest,
            "is_guest": True,
            "trainings": trainings
        }

    # 5. Пользователь не найден ни в users, ни в guests
    # Проверяем, есть ли training_uuid
    if not training_uuid:
        logger.warning(f"Гость {telegram_id} не имеет training_uuid")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Требуется training_uuid для регистрации гостя"
        )

    # Проверяем, существует ли тренировка с таким UUID
    training = db.get_training_by_uuid(training_uuid)
    if not training:
        logger.warning(f"Тренировка {training_uuid} не найдена")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тренировка не найдена"
        )

    # Добавляем гостя и записываем на тренировку
    signup = db.add_guest_signup(
        telegram_id=telegram_id,
        training_uuid=training_uuid,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        photo_url=user_data.photo_url
    )

    if not signup:
        logger.error(f"Ошибка добавления гостя {telegram_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при регистрации гостя"
        )

    # Получаем данные гостя
    guest = db.get_guest_by_telegram(telegram_id)

    # Создаём токены
    token_data = {
        "sub": str(telegram_id),
        "username": user_data.username,
        "is_guest": True
    }

    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )

    set_auth_cookies(response, access_token, refresh_token)

    logger.info(f"Гость {telegram_id} зарегистрирован на тренировку {training_uuid}")
    return {
        "success": True,
        "message": "Авторизация успешна",
        "user": guest,
        "is_guest": True,
        "trainings": [signup]
    }


@app.get("/api/guest/me")
async def get_guest_me(request: Request):
    """
    Получение текущей информации о госте (требует авторизации)
    Возвращает список тренировок гостя
    """
    # Получаем пользователя из токена
    user = get_current_user_from_access_token(request)

    # Если не получилось, проверяем cookie напрямую
    if not user:
        access_token = request.cookies.get("access_token")
        if access_token:
            try:
                payload = decode_token(access_token, "access")
                telegram_id = payload.get("sub")
                if telegram_id:
                    # Проверяем, гость ли это
                    if db.is_guest(int(telegram_id)):
                        guest = db.get_guest_by_telegram(int(telegram_id))
                        user = {**guest, 'is_guest': True, 'telegram_id': int(telegram_id)}
            except:
                pass

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )

    telegram_id = user.get('telegram_id')
    is_guest = user.get('is_guest', False)

    if not is_guest:
        # Если не гость, возвращаем информацию как обычный пользователь
        return {
            "telegram_id": telegram_id,
            "first_name": user.get('first_name'),
            "last_name": user.get('last_name'),
            "username": user.get('username'),
            "photo_url": user.get('photo_url'),
            "trainings": [],
            "is_active": user.get('is_active', True),
            "is_guest": False
        }

    # Получаем информацию о госте
    guest = db.get_guest_by_telegram(telegram_id)

    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Гость не найден"
        )

    # Получаем список тренировок гостя
    trainings = db.get_guest_trainings(telegram_id)

    return {
        "telegram_id": guest['telegram_id'],
        "first_name": guest['first_name'],
        "last_name": guest.get('last_name'),
        "username": guest.get('username'),
        "photo_url": guest.get('photo_url'),
        "trainings": trainings,
        "is_active": guest['is_active'],
        "is_guest": True
    }


@app.post("/api/guest/join/{training_uuid}")
async def guest_join_training(training_uuid: str, request: Request, response: Response):
    """
    Запись гостя на тренировку по ссылке-приглашению

    Проверяет валидность UUID и добавляет запись в guest_signups
    """
    # Получаем пользователя из токена (опционально)
    user = get_current_user_from_access_token(request)

    body = await request.json()
    telegram_id = body.get('telegram_id')
    first_name = body.get('first_name')
    last_name = body.get('last_name')
    username = body.get('username')
    photo_url = body.get('photo_url')

    if not all([telegram_id, first_name]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Требуется telegram_id и first_name"
        )

    # Проверяем валидность UUID
    training = db.get_training_by_uuid(training_uuid)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тренировка не найдена"
        )

    # Проверяем, существует ли уже пользователь в users
    existing_user = db.get_user_by_telegram_id(telegram_id)
    if existing_user and not existing_user.get('is_guest', False):
        logger.info(f"Пользователь {telegram_id} уже существует в users как не-гость")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже зарегистрированы как пользователь. Используйте обычную авторизацию."
        )
    
    # Если пользователь уже есть как гость (is_guest=1) — просто записываем на тренировку
    if existing_user and existing_user.get('is_guest', False):
        logger.info(f"Гость {telegram_id} уже существует, записываем на тренировку")

    # Проверяем, записан ли уже гость на эту тренировку
    is_signed_up = db.is_guest_signed_up(telegram_id, training_uuid)
    if is_signed_up:
        logger.info(f"Гость {telegram_id} уже записан на эту тренировку")
        return {
            "success": True,
            "message": "Вы уже записаны на эту тренировку",
            "is_guest": True,
            "training_uuid": training_uuid
        }

    # Добавляем запись гостя на тренировку
    signup = db.add_guest_signup(
        telegram_id=telegram_id,
        training_uuid=training_uuid,
        first_name=first_name,
        last_name=last_name,
        username=username,
        photo_url=photo_url
    )

    if not signup:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при записи гостя"
        )

    logger.info(f"Гость {telegram_id} записан на тренировку {training_uuid}")
    return {
        "success": True,
        "message": "Вы успешно записаны на тренировку",
        "is_guest": True,
        "training_uuid": training_uuid
    }


@app.post("/api/guest/leave/{training_uuid}")
async def guest_leave_training(
    training_uuid: str,
    request: Request
):
    """
    Отписка гостя от тренировки
    """
    # Получаем пользователя из токена
    user = get_current_user_from_access_token(request)

    # Если не получилось, проверяем cookie напрямую
    if not user:
        access_token = request.cookies.get("access_token")
        if access_token:
            try:
                payload = decode_token(access_token, "access")
                telegram_id = payload.get("sub")
                if telegram_id:
                    # Проверяем, гость ли это
                    if db.is_guest(int(telegram_id)):
                        guest = db.get_guest_by_telegram(int(telegram_id))
                        user = {**guest, 'is_guest': True, 'telegram_id': int(telegram_id)}
            except:
                pass

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )

    telegram_id = user.get('telegram_id')
    is_guest = user.get('is_guest', False)

    if not is_guest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Только гости могут использовать этот endpoint"
        )

    # Проверяем, что гость записан на эту тренировку
    is_signed_up = db.is_guest_signed_up(telegram_id, training_uuid)
    if not is_signed_up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вы не записаны на эту тренировку"
        )

    # Удаляем запись
    result = db.remove_guest_signup(telegram_id, training_uuid)

    if result.get('success'):
        logger.info(f"Гость {telegram_id} отписался от тренировки {training_uuid}")
        return {
            "success": True,
            "message": "Вы успешно отписались от тренировки"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Ошибка при отписке')
        )


# ==================== API для админки (управление гостями) ====================

@app.get("/api/admin/guests")
async def get_all_guests(
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Получение списка всех гостей с пагинацией (только для администраторов)
    """
    require_admin(user)
    
    guests = db.get_all_guests(limit=limit, offset=offset)
    
    return {
        "guests": guests,
        "total": len(guests),
        "limit": limit,
        "offset": offset
    }


@app.patch("/api/admin/guests/{telegram_id}/status")
async def update_guest_status(
    telegram_id: int,
    status_update: GuestStatusUpdate,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Активация/деактивация гостя (только для администраторов)
    """
    require_admin(user)
    
    # Проверяем, существует ли гость
    guest = db.get_guest_by_telegram(telegram_id)
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Гость не найден"
        )
    
    result = db.update_guest_status(telegram_id, status_update.is_active)
    
    if result.get('success'):
        return {
            "success": True,
            "message": f"Гость {'активирован' if status_update.is_active else 'деактивирован'}",
            "is_active": status_update.is_active
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Ошибка обновления статуса')
        )


@app.post("/api/admin/guests/{telegram_id}/convert")
async def convert_guest_to_user(
    telegram_id: int,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Конвертация гостя в пользователя (только для администраторов)
    """
    require_admin(user)
    
    # Проверяем, существует ли гость
    guest = db.get_guest_by_telegram(telegram_id)
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Гость не найден"
        )
    
    # Конвертируем
    new_user = db.convert_guest_to_user(
        telegram_id=telegram_id,
        first_name=guest.get('first_name'),
        last_name=guest.get('last_name'),
        username=guest.get('username'),
        photo_url=guest.get('photo_url')
    )
    
    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при конвертации гостя"
        )
    
    logger.info(f"Гость {telegram_id} конвертирован в пользователя")
    return {
        "success": True,
        "message": "Гость конвертирован в пользователя",
        "user": new_user
    }


@app.delete("/api/admin/guests/{telegram_id}")
async def delete_guest(
    telegram_id: int,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Удаление гостя (только для администраторов)
    """
    require_admin(user)
    
    # Проверяем, существует ли гость
    guest = db.get_guest_by_telegram(telegram_id)
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Гость не найден"
        )
    
    result = db.delete_guest(telegram_id)
    
    if result.get('success'):
        return {
            "success": True,
            "message": "Гость удалён"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Ошибка удаления гостя')
        )


@app.get("/api/admin/users", response_model=List[UserInfo])
async def get_all_users(
    filter: Optional[str] = None,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Получение списка всех пользователей (только для администраторов)
    
    Args:
        filter: Фильтр пользователей (active, inactive, guests)
    """
    require_admin(user)
    users = db.get_all_users(filter_type=filter)
    return users


# ==================== API для управления ботом ====================

class PollTemplate(BaseModel):
    """Модель шаблона опроса"""
    name: str
    description: str
    training_day: str
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
    start_time: str
    end_time: str
    location: str = "ВГАФК"
    enabled: bool = True

    @validator('start_time', 'end_time')
    def validate_time(cls, v):
        import re
        time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
        if not time_pattern.match(v):
            raise ValueError('Неверный формат времени (ожидается HH:MM)')
        return v


@app.get("/api/user/template")
async def get_template(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение шаблона опроса по умолчанию (доступно всем авторизованным)
    """
    require_auth(user)
    template = db.get_default_template()
    return {"template": template}


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
    
    # Topic ID только с Chat ID
    if schedule.message_thread_id and not schedule.chat_id:
        raise HTTPException(status_code=400, detail="Topic ID доступен только при наличии Chat ID")
    
    schedule_dict = schedule.dict()
    schedule_dict['id'] = str(uuid.uuid4())
    # Формируем training_time из start_time и end_time для обратной совместимости
    schedule_dict['training_time'] = f"{schedule.start_time} - {schedule.end_time}"
    
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


@app.delete("/api/admin/settings/active_polls/{poll_id}")
async def remove_active_poll(poll_id: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Удаление активного опроса (останавливает в Telegram + удаляет из БД)
    """
    require_admin(user)

    # Получаем опрос из БД
    poll = db.get_active_poll(poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Опрос не найден")

    # Вызываем API бота для удаления опроса из Telegram
    bot_api_key = os.getenv('BOT_API_KEY', 'volleybot_secret_key')
    bot_api_url = 'http://127.0.0.1:8001/api/delete_poll'

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                bot_api_url,
                json={
                    'chat_id': poll['chat_id'],
                    'message_id': poll['message_id'],
                    'action': 'delete'  # Полное удаление сообщения
                },
                headers={'X-API-Key': bot_api_key},
                timeout=30
            )
            api_result = response.json()

            if response.status_code != 200 or not api_result.get('success'):
                logger.warning(f"API бота вернуло ошибку: {api_result}")
                # Не прерываем удаление из БД, даже если бот не ответил
    except Exception as e:
        logger.error(f"Ошибка вызова API бота: {e}")
        # Продолжаем удаление из БД

    # Удаляем опрос из БД
    db.remove_active_poll(poll_id)

    return {"success": True, "message": "Опрос удалён"}


@app.post("/api/admin/settings/active_polls/{poll_id}/stop")
async def stop_active_poll(poll_id: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Остановка активного опроса (без удаления из БД)
    """
    require_admin(user)

    # Получаем опрос из БД
    poll = db.get_active_poll(poll_id)
    if not poll:
        raise HTTPException(status_code=404, detail="Опрос не найден")

    # Вызываем API бота для остановки опроса в Telegram
    bot_api_key = os.getenv('BOT_API_KEY', 'volleybot_secret_key')
    bot_api_url = 'http://127.0.0.1:8001/api/delete_poll'

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                bot_api_url,
                json={
                    'chat_id': poll['chat_id'],
                    'message_id': poll['message_id'],
                    'action': 'stop'  # Остановка голосования
                },
                headers={'X-API-Key': bot_api_key},
                timeout=30
            )
            api_result = response.json()

            # Если flood control или другая ошибка — всё равно считаем успехом
            if response.status_code != 200:
                logger.warning(f"API бота вернуло ошибку: {api_result}")
            elif not api_result.get('success'):
                logger.warning(f"API бота вернуло ошибку: {api_result}")
    except httpx.RequestError as e:
        logger.error(f"Ошибка вызова API бота: {e}")

    # Обновляем статус опроса в БД
    cursor = db.conn.cursor()
    cursor.execute('''
        UPDATE active_polls SET status = 'stopped' WHERE id = ?
    ''', (poll_id,))
    db.conn.commit()

    return {"success": True, "message": "Опрос остановлен"}


@app.get("/api/admin/settings/admin_ids")
async def get_admin_ids(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение списка ID администраторов
    """
    require_admin(user)
    admin_ids = db.get_admin_ids()
    return {"admin_ids": admin_ids}


@app.get("/api/admin/stats")
async def get_stats(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение статистики для дашборда (только для администраторов)
    """
    require_admin(user)

    # Получаем количество записей за 30 дней (тренировки + игры)
    registrations_count = db.get_registrations_count(days=30)

    # Получаем последние активности (тренировки + игры)
    recent_activities = db.get_recent_activities(limit=10)

    return {
        "admin_count": db.get_admin_count(),
        "users_count": db.get_users_count(),
        "registrations_count": registrations_count,
        "recent_activities": recent_activities,
        "schedules_count": len(db.get_poll_schedules()),
        "active_polls_count": len(db.get_active_polls())
    }


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
    
    # Используем метод remove_admin_id из database
    db.remove_admin_id(int(admin_id))

    return {"success": True, "message": "Администратор удалён"}



# ==================== Универсальные ссылки на тренировки ====================

@app.get("/training/{training_uuid}")
async def get_training_redirect(training_uuid: str, request: Request):
    """
    Универсальная ссылка на тренировку
    Возвращает JSON с редиректом для обработки на фронте
    Логика:
    1. Если не авторизован → redirect на /login?redirect=/t/{uuid}
    2. Если гость → redirect на /guest/training/{uuid}
    3. Если пользователь → redirect на /dashboard/calendar?training={uuid}
    """
    # Получаем пользователя из токена
    user = get_current_user_from_access_token(request)

    # Проверяем тренировку
    training = db.get_training_by_uuid(training_uuid)
    if not training:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    # Если пользователь не авторизован → редирект на логин с /t/{uuid} (не /guest/training/{uuid}!)
    if not user:
        return {"redirect": f"/login?redirect=/t/{training_uuid}"}

    # Проверяем, является ли пользователь гостем
    is_guest = db.is_guest(user.get('telegram_id'))

    if is_guest:
        # Гость → страница гостя
        return {"redirect": f"/guest/training/{training_uuid}"}
    else:
        # Пользователь → календарь с открытой модалкой
        return {"redirect": f"/dashboard/calendar?training={training_uuid}"}

@app.get("/api/user/calendar")
async def get_calendar(year: int, month: int, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение календаря событий на месяц (новая архитектура events)
    Возвращает все события месяца с записями
    """
    # Получаем все события из новой таблицы events
    events = db.get_events(year, month)
    
    # Группируем события по типу
    trainings = []
    games_list = []
    
    for event in events:
        event_id = event['id']
        event_uuid = event.get('uuid')
        event_type = event['event_type']
        
        # Получаем участников события
        participants = db.get_event_participants(event_id)
        
        # Формируем структуру данных
        event_data = {
            'id': event_id,
            'uuid': event_uuid,
            'event_type': event_type,
            'name': event.get('name', ''),
            'date': event.get('date'),
            'time': event.get('start_time'),  # Для обратной совместимости
            'start_time': event.get('start_time'),
            'end_time': event.get('end_time'),
            'location': event.get('location', ''),
            'chat_id': event.get('chat_id'),  # Нужно для записи
            'topic_id': event.get('topic_id'),  # Нужно для записи
            'opponent': event.get('opponent'),
            'result': event.get('result'),
            'score': event.get('score'),
            'participants': participants,
            'registrations': participants,  # Для обратной совместимости с модалкой
            'registered_count': len([p for p in participants if p.get('status') == 'registered']),
            'waitlist_count': len([p for p in participants if p.get('status') == 'waitlist']),
        }
        
        # Проверяем записан ли текущий пользователь
        if user:
            user_telegram_id = user.get('telegram_id')
            user_participant = next((p for p in participants if p.get('telegram_id') == user_telegram_id), None)
            event_data['user_status'] = user_participant['status'] if user_participant else None
            event_data['is_guest'] = user_participant.get('is_guest', False) if user_participant else False
        else:
            event_data['user_status'] = None
            event_data['is_guest'] = False
        
        # Распределяем по типам
        if event_type in ['training', 'scheduled_training', 'one_time_training']:
            trainings.append(event_data)
        elif event_type == 'game':
            games_list.append(event_data)
    
    # Для обратной совместимости добавляем данные из старых таблиц
    # (если есть события которые ещё не перенесены в events)
    # И используем старый формат для фронтенда

    # Старые тренировки из scheduled_trainings
    scheduled_trainings = db.get_scheduled_trainings(year, month)
    for training in scheduled_trainings:
        training_uuid = training.get('uuid')
        training_id = training.get('id')
        
        # Проверяем, есть ли уже в events
        existing = next((t for t in trainings if t.get('uuid') == training_uuid), None)
        if not existing:
            participants = db.get_training_registrations(
                training.get('training_date', ''),
                training.get('training_time', ''),
                training.get('chat_id', '')
            )
            trainings.append({
                'id': training_id,
                'uuid': training_uuid,
                'event_type': 'scheduled_training',
                'name': training.get('name', 'Тренировка'),
                'date': training.get('training_date'),
                'time': training.get('training_time'),
                'start_time': training.get('start_time'),
                'end_time': training.get('end_time'),
                'location': training.get('location', ''),
                'chat_id': training.get('chat_id'),
                'topic_id': training.get('topic_id'),
                'registrations': participants,  # Старый формат
                'participants': participants,   # Новый формат
                'registered_count': len([p for p in participants if p.get('status') == 'registered']),
                'waitlist_count': len([p for p in participants if p.get('status') == 'waitlist']),
                'user_status': None
            })
        else:
            # Добавляем старый формат для совместимости
            existing['time'] = existing.get('start_time')
            existing['registrations'] = existing.get('participants', [])

    # Старые игры из games
    old_games = db.get_all_games(year, month)
    for game in old_games:
        game_id = game.get('id')
        game_uuid = game.get('uuid')

        # Проверяем, есть ли уже в events
        existing = next((g for g in games_list if g.get('uuid') == game_uuid), None)
        if not existing:
            signups = db.get_game_signups(game_id)
            
            # Проверяем записан ли текущий пользователь
            user_status = None
            if user:
                user_telegram_id = user.get('telegram_id')
                user_signup = next((s for s in signups if s.get('user_telegram_id') == user_telegram_id), None)
                user_status = user_signup['status'] if user_signup else None
            
            games_list.append({
                'id': game_id,
                'uuid': game_uuid,
                'event_type': 'game',
                'name': game.get('name', ''),
                'date': game.get('date'),
                'time': game.get('start_time'),
                'start_time': game.get('start_time'),
                'end_time': game.get('end_time'),
                'location': game.get('location', ''),
                'opponent': game.get('opponent'),
                'result': game.get('result'),
                'score': game.get('score'),
                'signups': signups,         # Старый формат
                'participants': signups,    # Новый формат
                'registered_count': len(signups),
                'waitlist_count': 0,
                'user_status': user_status
            })
        else:
            # Добавляем старый формат для совместимости
            existing['time'] = existing.get('start_time')
            existing['signups'] = existing.get('participants', [])
    
    return {
        "trainings": trainings,
        "games": games_list
    }


# ==================== Новая архитектура: API для events ====================

@app.post("/api/events/{event_id}/signup")
async def signup_for_event(event_id: int, request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Запись на событие (новая архитектура events)
    """
    require_auth(user)
    
    # Получаем ID пользователя
    user_telegram_id = user.get('telegram_id')
    user_row = db.get_user_by_telegram_id(user_telegram_id)
    if not user_row:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_id = user_row['id']
    is_guest = user_row.get('is_guest', False)
    
    result = db.add_event_signup(event_id, user_id, is_guest)
    
    if result.get('success'):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Запись не удалась'))


@app.delete("/api/events/{event_id}/signup")
async def cancel_signup_for_event(event_id: int, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Отмена записи на событие (новая архитектура events)
    """
    require_auth(user)
    
    # Получаем ID пользователя
    user_telegram_id = user.get('telegram_id')
    user_row = db.get_user_by_telegram_id(user_telegram_id)
    if not user_row:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_id = user_row['id']
    
    result = db.remove_event_signup(event_id, user_id)
    
    if result.get('success'):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Отмена не удалась'))


@app.get("/api/events/{event_uuid}")
async def get_event(event_uuid: str, request: Request):
    """
    Получение события по UUID (новая архитектура events)
    """
    event = db.get_event_by_uuid(event_uuid)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    # Получаем участников
    participants = db.get_event_participants(event['id'])
    event['participants'] = participants
    event['registered_count'] = len([p for p in participants if p.get('status') == 'registered'])
    event['waitlist_count'] = len([p for p in participants if p.get('status') == 'waitlist'])
    
    # Проверяем авторизацию
    user = get_current_user_from_access_token(request)
    if user:
        user_telegram_id = user.get('telegram_id')
        user_participant = next((p for p in participants if p.get('telegram_id') == user_telegram_id), None)
        event['user_status'] = user_participant['status'] if user_participant else None
        event['is_guest'] = user_participant.get('is_guest', False) if user_participant else False
    
    return event


# ==================== Старая архитектура: API для тренировок ====================

@app.post("/api/user/calendar/register")
async def register_for_training(request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Запись на тренировку по UUID
    """
    require_auth(user)

    body = await request.json()
    training_uuid = body.get('uuid')

    if not training_uuid:
        raise HTTPException(status_code=400, detail="Missing uuid")

    user_telegram_id = user.get('telegram_id')

    # Находим event по UUID
    event = db.get_event_by_uuid(training_uuid)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    # Записываем пользователя на событие
    result = db.add_event_signup_to_training(event['id'], user_telegram_id)

    if result.get('success'):
        return {"success": True, "status": result.get('status')}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Registration failed'))


@app.post("/api/user/calendar/unregister")
async def unregister_from_training(request: Request, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Отписка от тренировки по UUID
    """
    require_auth(user)

    body = await request.json()
    training_uuid = body.get('uuid')

    if not training_uuid:
        raise HTTPException(status_code=400, detail="Missing uuid")

    user_telegram_id = user.get('telegram_id')

    # Находим event по UUID
    event = db.get_event_by_uuid(training_uuid)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")

    # Отписываем пользователя от события
    result = db.remove_event_signup_by_telegram(event['id'], user_telegram_id)

    if result.get('success'):
        return {"success": True}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Unregistration failed'))


@app.delete("/api/admin/calendar/remove-user/{training_date}/{training_time}/{chat_id}/{user_telegram_id}")
async def admin_remove_user_from_training(
    training_date: str,
    training_time: str,
    chat_id: str,
    user_telegram_id: int,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Удаление участника из тренировки администратором
    """
    require_admin(user)

    result = db.admin_remove_user_from_training(
        training_date, training_time, chat_id, user_telegram_id
    )

    if result.get('success'):
        return {"success": True, "removed_status": result.get('removed_status')}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to remove user'))


@app.get("/api/user/my-trainings")
async def get_my_trainings(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение моих записей на тренировки и игры
    """
    require_auth(user)

    user_telegram_id = user.get('telegram_id')

    # Получаем тренировки
    trainings = db.get_user_trainings(user_telegram_id)

    # Получаем игры
    games = db.get_user_games(user_telegram_id)

    # Объединяем в один список с указанием типа
    all_items = []

    for training in trainings:
        all_items.append({
            **training,
            'type': 'training'
        })

    for game in games:
        all_items.append({
            **game,
            'type': 'game'
        })

    # Сортируем по дате
    all_items.sort(key=lambda x: x.get('training_date') or x.get('date') or '')

    return {"items": all_items}


# ==================== API для админов (Users & Trainings) ====================

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
    Полное удаление пользователя (только админы)
    """
    require_admin(user)

    result = db.delete_web_user(telegram_id)

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
    start_time = body.get('start_time')
    end_time = body.get('end_time')
    chat_id = body.get('chat_id')
    topic_id = body.get('topic_id')
    name = body.get('name', 'Тренировка')
    location = body.get('location', 'ВГАФК')
    
    # Формируем training_time из start_time и end_time
    training_time = f"{start_time} - {end_time}" if start_time and end_time else ''

    # Валидация обязательных полей
    if not all([training_date, start_time, end_time, chat_id]):
        raise HTTPException(status_code=400, detail="Заполните обязательные поля: дата, время начала, время окончания, chat_id")

    # Валидация времени начала и окончания
    import re
    time_pattern = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
    if not time_pattern.match(start_time):
        raise HTTPException(status_code=400, detail="Неверный формат start_time (ожидается HH:MM)")
    if not time_pattern.match(end_time):
        raise HTTPException(status_code=400, detail="Неверный формат end_time (ожидается HH:MM)")
    
    # Проверка что end_time >= start_time (с учётом перехода через полночь)
    try:
        start_parts = list(map(int, start_time.split(':')))
        end_parts = list(map(int, end_time.split(':')))
        start_minutes = start_parts[0] * 60 + start_parts[1]
        end_minutes = end_parts[0] * 60 + end_parts[1]
        
        # Если end_time < start_time, считаем что тренировка через полночь
        if end_minutes < start_minutes:
            end_minutes += 24 * 60  # Добавляем 24 часа
        
        if end_minutes - start_minutes < 15:
            raise HTTPException(status_code=400, detail="Минимальная длительность тренировки 15 минут")
    except ValueError:
        raise HTTPException(status_code=400, detail="Ошибка парсинга времени")

    # Topic ID только с Chat ID
    if topic_id and not chat_id:
        raise HTTPException(status_code=400, detail="Topic ID доступен только при наличии Chat ID")

    # Формируем уникальный training_id с UUID для избежания коллизий
    import uuid
    training_id = f"{training_date}_{start_time}_{chat_id}_{str(uuid.uuid4())[:8]}"

    result = db.add_one_time_training(training_id, training_date, training_time, chat_id, topic_id, name, start_time, end_time, location)

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


@app.delete("/api/admin/events/{event_uuid}")
async def remove_event(event_uuid: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Удаление события по UUID (только админы)
    """
    require_admin(user)

    result = db.remove_event_by_uuid(event_uuid)

    if result.get('success'):
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to remove event'))


@app.get("/api/admin/trainings")
async def get_all_trainings(start_date: str, end_date: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение всех записей на тренировки за период (только админы)
    """
    require_admin(user)

    trainings = db.get_all_trainings(start_date, end_date)
    return {"trainings": trainings}


@app.get("/api/admin/games/signups")
async def get_all_game_signups(start_date: str, end_date: str, user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение всех записей на игры за период (только админы)
    """
    require_admin(user)

    signups = db.get_all_game_signups(start_date, end_date)
    return {"signups": signups}


# ==================== API для игр ====================

class GameCreate(BaseModel):
    """Модель создания игры"""
    name: str
    date: str
    location: Optional[str] = None
    start_time: Optional[str] = None
    opponent: Optional[str] = None
    chat_id: Optional[str] = None
    topic_id: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Товарищеский матч",
                "date": "2026-03-15",
                "location": "СК Звезда",
                "start_time": "19:00",
                "opponent": "Команда соперников",
                "chat_id": "-1001234567890",
                "topic_id": 42
            }
        }
    }


class GameResult(BaseModel):
    """Модель результата игры"""
    result: str  # win, loss, draw
    score: str  # например "3:1"


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


# ==================== API для игр ====================

@app.get("/api/games")
async def get_games(
    year: Optional[int] = None,
    month: Optional[int] = None,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Получение списка игр.
    Если указаны year и month — возвращает игры за месяц.
    """
    require_auth(user)
    
    games = db.get_all_games(year, month)
    return {"games": games}


@app.get("/api/games/{game_id}")
async def get_game(
    game_id: str,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Получение информации об игре
    """
    require_auth(user)

    game = db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    # Проверяем, является ли пользователь гостем и имеет ли доступ к этой тренировке
    is_guest = user.get('is_guest', False)
    if is_guest:
        telegram_id = user.get('telegram_id')
        game_uuid = game.get('uuid')
        # Проверяем, записан ли гость на эту тренировку
        is_signed_up = db.is_guest_signed_up(telegram_id, game_uuid)
        if not is_signed_up:
            logger.warning(f"Гость {telegram_id} попытался получить доступ к тренировке {game_uuid}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещён. Вы можете просматривать только тренировки, на которые записаны."
            )

    # Добавляем список записавшихся с флагом is_guest
    signups = db.get_game_signups(game_id)

    # Добавляем is_guest для каждого участника
    for signup in signups:
        signup_telegram_id = signup.get('user_telegram_id')
        signup['is_guest'] = db.is_guest(signup_telegram_id) if signup_telegram_id else False

    game['signups'] = signups
    
    # Проверяем записан ли текущий пользователь
    if user:
        user_telegram_id = user.get('telegram_id')
        user_signup = next((s for s in signups if s.get('user_telegram_id') == user_telegram_id), None)
        game['user_status'] = user_signup['status'] if user_signup else None
    else:
        game['user_status'] = None

    return {"game": game}


@app.get("/api/trainings/{training_uuid}")
async def get_training_by_uuid(
    training_uuid: str,
    request: Request
):
    """
    Получение тренировки по UUID

    Гости могут просматривать любую тренировку по UUID (UUID случайный, его нельзя подобрать)
    """
    # Получаем пользователя из токена (опционально)
    user = get_current_user_from_access_token(request)
    
    # Если пользователь не авторизован — проверяем, гость ли это
    if not user:
        # Проверяем cookie напрямую
        from fastapi import Cookie
        access_token = request.cookies.get("access_token")
        if access_token:
            try:
                payload = decode_token(access_token, "access")
                telegram_id = payload.get("sub")
                if telegram_id:
                    user = db.get_user_by_telegram_id(int(telegram_id))
                    # Проверяем, гость ли это
                    if not user and db.is_guest(int(telegram_id)):
                        guest = db.get_guest_by_telegram(int(telegram_id))
                        user = {**guest, 'is_guest': True}
            except:
                pass
    
    # Гости могут видеть любую тренировку по UUID (без ограничений)
    # UUID случайный, его нельзя подобрать
    
    # Получаем тренировку по UUID
    training = db.get_training_by_uuid(training_uuid)
    if not training:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    # Нормализуем поля для фронтенда
    # Для scheduled_trainings и one_time_trainings
    if 'training_date' in training:
        training['date'] = training['training_date']
    if 'training_time' in training:
        training['time'] = training['training_time']

    # Добавляем тип события для фронтенда
    if training.get('source') == 'one_time_trainings':
        training['event_type'] = 'one_time_training'
    elif training.get('source') == 'scheduled_trainings':
        training['event_type'] = 'scheduled_training'

    # Добавляем список участников с флагом is_guest
    participants = db.get_training_participants(training_uuid)
    training['registrations'] = participants
    training['registered_count'] = len([p for p in participants if p.get('status') == 'registered'])
    training['waitlist_count'] = len([p for p in participants if p.get('status') == 'waitlist'])

    # Добавляем статус записи текущего пользователя
    if user:
        telegram_id = user.get('telegram_id')
        user_signup = next((p for p in participants if int(p.get('user_telegram_id')) == telegram_id), None)
        training['user_status'] = user_signup['status'] if user_signup else None
    else:
        training['user_status'] = None

    return {"training": training}


@app.post("/api/admin/games")
async def create_game(
    game_data: GameCreate,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Создание новой игры (только админы)
    """
    require_admin(user)
    
    game_dict = game_data.model_dump()
    result = db.add_game(game_dict)
    
    if result.get('success'):
        return {
            "success": True,
            "id": result['id'],
            "message": "Игра создана"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to create game'))


@app.put("/api/admin/games/{game_id}")
async def update_game(
    game_id: str,
    game_data: GameCreate,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Обновление игры (только админы)
    """
    require_admin(user)
    
    # Проверяем существование
    existing = db.get_game(game_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    updates = game_data.model_dump(exclude_unset=True)
    result = db.update_game(game_id, updates)
    
    if result.get('success'):
        return {"success": True, "message": "Игра обновлена"}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to update game'))


@app.delete("/api/admin/games/{game_id}")
async def delete_game(
    game_id: str,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Удаление игры (только админы)
    """
    require_admin(user)
    
    result = db.remove_game(game_id)
    
    if result.get('success'):
        return {"success": True, "message": "Игра удалена"}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to delete game'))


@app.post("/api/games/{game_id}/signup")
async def signup_for_game(
    game_id: str,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Запись на игру (доступно всем авторизованным пользователям)
    Повторный вызов отменяет запись
    """
    require_auth(user)

    # Проверяем существование игры
    game = db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    telegram_id = user.get('telegram_id')
    result = db.signup_for_game(game_id, telegram_id)

    if result.get('success'):
        action = result.get('action', 'registered')
        return {
            "success": True,
            "action": action,
            "message": "Запись на игру" if action == 'registered' else "Запись отменена"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to signup'))


@app.post("/api/games/{game_id}/unregister")
async def unregister_from_game(
    game_id: str,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Отписка от игры (доступно всем авторизованным пользователям)
    """
    require_auth(user)

    # Проверяем существование игры
    game = db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    telegram_id = user.get('telegram_id')
    result = db.unregister_from_game(game_id, telegram_id)

    if result.get('success'):
        return {"success": True, "message": "Вы успешно выписались с игры"}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to unregister'))


@app.put("/api/admin/games/{game_id}/result")
async def set_game_result(
    game_id: str,
    result_data: GameResult,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Установка результата игры (только админы)
    """
    require_admin(user)

    # Проверяем существование
    game = db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    result = db.set_game_result(game_id, result_data.result, result_data.score)

    if result.get('success'):
        return {"success": True, "message": "Результат установлен"}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to set result'))


@app.delete("/api/admin/games/{game_id}/result")
async def clear_game_result(
    game_id: str,
    user: dict = Depends(get_current_user_from_access_cookie)
):
    """
    Сброс результата игры (только админы)
    """
    require_admin(user)

    # Проверяем существование
    game = db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    result = db.set_game_result(game_id, '', '')

    if result.get('success'):
        return {"success": True, "message": "Результат сброшен"}
    else:
        raise HTTPException(status_code=500, detail=result.get('error', 'Failed to clear result'))


@app.get("/api/games/my")
async def get_my_games(user: dict = Depends(get_current_user_from_access_cookie)):
    """
    Получение списка игр, на которые записан текущий пользователь
    """
    require_auth(user)

    telegram_id = user.get('telegram_id')
    games = db.get_user_games(telegram_id)

    return {"games": games}


# ==================== Запуск планировщика ====================

# Планируем добавление тренировок и опросов каждый день в 12:00 MSK
scheduler.add_job(
    add_trainings_and_polls_from_schedules,
    CronTrigger(hour=12, minute=0),
    id='daily_trainings_polls'
)

# Запускаем планировщик
scheduler.start()
logger.info("Планировщик запущен: добавление тренировок и опросов в 12:00")


# ==================== Статика ====================

static_path = Path("/var/www/volleyteam.ru")
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
    index_path = Path("/var/www/volleyteam.ru") / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "VolleyBot Auth API - build not found"}
