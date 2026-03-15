#!/usr/bin/env python3
"""
Volleyball Poll Bot - продвинутый Telegram-бот для управления опросами о посещении волейбольных тренировок
"""

import os
import logging
import uuid
import httpx
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Получаем директорию скрипта для абсолютных путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Настраиваем логирование httpx ДО импорта telegram
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Очищаем handler'ы httpx до импорта telegram
httpx_logger = logging.getLogger('httpx')
httpx_logger.handlers = []
httpx_logger.propagate = True

from telegram import Update, Bot, Poll, Message, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from database import Database
from utils import get_weekday_russian, get_next_occurrence, get_next_sunday, format_date_with_weekday, get_day_of_week_number
from handlers import start, get_user_id, handle_message, button_handler, creation_states, show_stats


logger = logging.getLogger(__name__)

# Фильтр для маскировки токена и фильтрации getUpdates
class TokenMaskingFilter(logging.Filter):
    """Фильтр для маскировки токена и фильтрации getUpdates"""

    _token = None

    @classmethod
    def set_token(cls, token):
        cls._token = token

    def filter(self, record):
        if not self._token:
            return True

        msg = record.getMessage() if hasattr(record, 'getMessage') else str(record.msg)

        # Пропускаем getUpdates с 200 OK
        if '/getUpdates' in msg and '200 OK' in msg:
            return False

        return True


# Formatter с маскировкой токена
class TokenMaskingFormatter(logging.Formatter):
    """Formatter который маскирует токен в отформатированном сообщении"""

    _token = None

    @classmethod
    def set_token(cls, token):
        cls._token = token

    def __init__(self, fmt=None, datefmt=None, style='%', validate=True):
        super().__init__(fmt, datefmt, style, validate)

    def format(self, record):
        original = super().format(record)
        if self._token:
            return original.replace(self._token, '***')
        return original


# Применяем фильтр ко всем handler'ам
token_filter = TokenMaskingFilter()
for handler in logging.root.handlers[:]:
    handler.addFilter(token_filter)
    if handler.formatter:
        old_fmt = handler.formatter._fmt
        new_formatter = TokenMaskingFormatter(fmt=old_fmt)
        handler.setFormatter(new_formatter)


class VolleyBot:
    """
    Основной класс бота для управления опросами волейбольных тренировок
    """

    def __init__(self, token_file: str = ".bot_token", db_path: str = "volleybot.db"):
        self.token_file = os.path.join(BASE_DIR, token_file)
        self.bot_token = self.load_bot_token(self.token_file)

        # Инициализация базы данных
        self.db = Database(os.path.join(BASE_DIR, db_path))

        # Проверка инициализации базы данных
        if not self.db.is_initialized():
            logger.error("=" * 60)
            logger.error("База данных не инициализирована!")
            logger.error("Для инициализации запустите: python3 init_db.py")
            logger.error("=" * 60)
            print("\n❌ База данных не инициализирована!")
            print("📝 Для инициализации запустите: python3 init_db.py\n")
            import sys
            sys.exit(1)

        # Получаем список администраторов из БД
        self.admin_user_ids = self.db.get_admin_ids()

    def load_bot_token(self, token_file: str) -> str:
        """Загрузка токена бота из отдельного файла"""
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                token = f.read().strip()
                if not token:
                    raise ValueError("Токен пустой")
                return token
        except FileNotFoundError:
            logger.error(f"Файл токена {token_file} не найден. Создайте файл и поместите в него токен бота.")
            raise
        except Exception as e:
            logger.error(f"Ошибка при чтении токена: {e}")
            raise

    def get_default_template(self) -> Dict[str, Any]:
        """Получение дефолтного шаблона опроса"""
        return self.db.get_default_template()

    def update_default_template(self, updated_template: Dict[str, Any]):
        """Обновление дефолтного шаблона опроса"""
        self.db.set_default_template(updated_template)

    def get_poll_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Получение шаблона опроса по ID"""
        if template_id == 'default':
            default_template = self.get_default_template()
            if default_template:
                template_copy = default_template.copy()
                template_copy['id'] = 'default'
                return template_copy
        elif template_id == 'scheduled':
            default_template = self.get_default_template()
            if default_template:
                template_copy = default_template.copy()
                template_copy['id'] = 'scheduled'
                return template_copy
        elif template_id == 'single':
            default_template = self.get_default_template()
            if default_template:
                template_copy = default_template.copy()
                template_copy['id'] = 'single'
                return template_copy
        return None

    def get_poll_templates(self) -> List[Dict[str, Any]]:
        """Получение всех шаблонов опросов (для совместимости)"""
        default_template = self.get_default_template()
        if default_template:
            template_copy = default_template.copy()
            template_copy['id'] = 'default'
            return [template_copy]
        return []

    async def create_poll(self, bot: Bot, chat_id: str, question: str, options: List[str],
                         is_anonymous: bool = False, message_thread_id: Optional[int] = None) -> Optional[Message]:
        """Создание опроса в указанном чате или топике"""
        try:
            # Прямой запрос к API через httpx для обхода проблемы сериализации options
            data = {
                'chat_id': chat_id,
                'question': question,
                'options': json.dumps(options, ensure_ascii=False),  # Сериализуем как JSON строку
                'is_anonymous': is_anonymous,
                'allows_multiple_answers': False
            }
            if message_thread_id is not None:
                data['message_thread_id'] = message_thread_id
            
            # Получаем токен из бота
            token = bot._bot.token
            
            # Используем httpx напрямую
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'https://api.telegram.org/bot{token}/sendPoll',
                    json=data,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
            
            # Создаем Message из результата
            from telegram import Message
            if result.get('ok'):
                message = Message.de_json(result['result'], bot)
                return message
            else:
                logger.error(f"Telegram API error: {result}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при создании опроса в чате {chat_id}{' (топик ' + str(message_thread_id) + ')' if message_thread_id else ''}: {e}")
            return None

    async def pin_message(self, bot: Bot, chat_id: str, message_id: int) -> bool:
        """Закрепление сообщения в чате"""
        try:
            await bot.pin_chat_message(chat_id=chat_id, message_id=message_id)
            return True
        except Exception as e:
            logger.error(f"Ошибка при закреплении сообщения {message_id} в чате {chat_id}: {e}")
            return False

    async def unpin_all_messages(self, bot: Bot, chat_id: str) -> bool:
        """Открепление всех сообщений в чате"""
        try:
            await bot.unpin_all_chat_messages(chat_id=chat_id)
            return True
        except Exception as e:
            logger.error(f"Ошибка при откреплении сообщений в чате {chat_id}: {e}")
            return False

    async def send_message(self, bot: Bot, chat_id: str, text: str) -> Optional[Message]:
        """Отправка текстового сообщения в чат"""
        try:
            message = await bot.send_message(chat_id=chat_id, text=text)
            return message
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в чат {chat_id}: {e}")
            return None

    async def stop_poll(self, bot: Bot, chat_id: str, message_id: int) -> bool:
        """Остановка опроса"""
        try:
            await bot.stop_poll(chat_id=chat_id, message_id=message_id)
            return True
        except Exception as e:
            logger.error(f"Ошибка при остановке опроса {message_id} в чате {chat_id}: {e}")
            return False

    async def delete_message(self, bot: Bot, chat_id: str, message_id: int) -> bool:
        """Удаление сообщения из чата"""
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения {message_id} из чата {chat_id}: {e}")
            return False

    async def get_poll_results(self, bot: Bot, chat_id: str, message_id: int) -> Optional[Poll]:
        """Получение результатов опроса"""
        try:
            poll = await bot.stop_poll(chat_id=chat_id, message_id=message_id)
            return poll
        except Exception as e:
            logger.error(f"Ошибка при получении результатов опроса {message_id} в чате {chat_id}: {e}")
            return None

    async def create_poll_from_template(self, bot: Bot, chat_id: str, message_thread_id: Optional[int] = None) -> Optional[Message]:
        """Создание опроса из дефолтного шаблона"""
        template = self.get_default_template()
        if not template:
            logger.error("Дефолтный шаблон опроса не найден")
            return None

        training_day = template['training_day']
        start_time = template.get('start_time', template.get('training_time', '18:00'))
        end_time = template.get('end_time', '20:00')
        location = template.get('location', '')
        name = template.get('name', 'Тренировка')

        target_day = get_day_of_week_number(training_day)
        if target_day == -1:
            logger.error(f"Неверный день недели: {training_day}")
            return None

        now = datetime.now()
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        next_training_date = now + timedelta(days=days_ahead)
        formatted_date_with_weekday = format_date_with_weekday(next_training_date)

        # Формируем описание с новыми переменными
        description = template['description']
        description = description.replace('{date}', formatted_date_with_weekday)
        description = description.replace('{start_time}', start_time)
        description = description.replace('{end_time}', end_time)
        description = description.replace('{time}', f"{start_time} - {end_time}")  # Для обратной совместимости
        description = description.replace('{location}', location)
        description = description.replace('{name}', name)

        poll_message = await self.create_poll(
            bot=bot,
            chat_id=chat_id,
            question=description,
            options=template['options'],
            is_anonymous=False,
            message_thread_id=message_thread_id
        )

        if poll_message:
            await self.pin_message(bot, chat_id, poll_message.message_id)
            logger.info(f"Опрос создан из дефолтного шаблона в чате {chat_id}{' (топик ' + str(message_thread_id) + ')' if message_thread_id else ''}")

        return poll_message

    def add_poll_schedule(self, schedule: Dict[str, Any]):
        """Добавление расписания опроса"""
        self.db.add_poll_schedule(schedule)

    def get_poll_schedules(self) -> List[Dict[str, Any]]:
        """Получение всех расписаний опросов"""
        return self.db.get_poll_schedules()

    def remove_poll_schedule(self, schedule_id: str):
        """Удаление расписания опроса"""
        self.db.remove_poll_schedule(schedule_id)

    async def create_polls_for_all_enabled_templates(self, bot: Bot):
        """Создание опросов по всем активным расписаниям"""
        schedules = self.get_poll_schedules()
        for schedule in schedules:
            if schedule.get('enabled', True):
                poll_day = schedule.get('poll_day', 'sunday')
                target_day = get_day_of_week_number(poll_day)
                if target_day is not None and target_day == datetime.now().weekday():
                    await self.create_poll_from_schedule(bot, schedule)

    async def create_poll_from_schedule(self, bot: Bot, schedule: Dict[str, Any]):
        """Создание опроса из расписания"""
        chat_id = schedule['chat_id']
        thread_id = schedule.get('message_thread_id', None)
        training_day = schedule['training_day']
        
        # Получаем новые поля или используем старые для обратной совместимости
        start_time = schedule.get('start_time', schedule.get('training_time', '18:00').split(' - ')[0].strip())
        end_time = schedule.get('end_time', schedule.get('training_time', '18:00 - 20:00').split(' - ')[1].strip() if ' - ' in schedule.get('training_time', '') else '20:00')
        location = schedule.get('location', '')
        name = schedule.get('name', 'Тренировка')
        options = schedule.get('options', [])

        target_day = get_day_of_week_number(training_day)
        if target_day == -1:
            logger.error(f"Неверный день недели: {training_day}")
            return None

        now = datetime.now()
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        next_training_date = now + timedelta(days=days_ahead)
        formatted_date_with_weekday = format_date_with_weekday(next_training_date)

        template = self.get_default_template()
        
        # Формируем описание с новыми переменными
        description = template['description']
        description = description.replace('{date}', formatted_date_with_weekday)
        description = description.replace('{start_time}', start_time)
        description = description.replace('{end_time}', end_time)
        description = description.replace('{time}', f"{start_time} - {end_time}")  # Для обратной совместимости
        description = description.replace('{location}', location)
        description = description.replace('{name}', name)

        poll_options = options if options else template['options']

        poll_message = await self.create_poll(
            bot=bot,
            chat_id=chat_id,
            question=description,
            options=poll_options,
            is_anonymous=False,
            message_thread_id=thread_id
        )

        if poll_message:
            logger.info(f"Опрос создан из расписания {schedule['id']} в чате {chat_id}")

        return poll_message

    def save_config(self):
        """Сохранение конфигурации (для совместимости)"""
        pass

    def add_poll_template(self, template: Dict[str, Any]):
        """Добавление шаблона опроса (для совместимости)"""
        pass


# Экземпляр бота
volley_bot = VolleyBot(db_path="volleybot.db")

# Устанавливаем токен в фильтр и formatter
TokenMaskingFilter.set_token(volley_bot.bot_token)
TokenMaskingFormatter.set_token(volley_bot.bot_token)


# ==================== HTTP API для веб-сервера ====================

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class BotAPIHandler(BaseHTTPRequestHandler):
    """HTTP обработчик для API бота"""

    def do_POST(self):
        """Обработка POST запросов"""
        if self.path == '/api/create_poll':
            # Получаем данные из тела запроса
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Проверяем авторизацию (простой секретный ключ)
            api_key = self.headers.get('X-API-Key', '')
            expected_key = os.getenv('BOT_API_KEY', 'volleybot_secret_key')

            if api_key != expected_key:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
                return

            try:
                # Извлекаем параметры
                chat_id = data.get('chat_id')
                topic_id = data.get('topic_id')
                training_date = data.get('training_date')
                start_time = data.get('start_time')
                end_time = data.get('end_time')
                location = data.get('location')
                name = data.get('name', 'Тренировка')

                if not all([chat_id, training_date, start_time, end_time]):
                    raise ValueError("Missing required fields")

                # Создаём опрос через бота
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        create_poll_via_bot(
                            chat_id=chat_id,
                            topic_id=topic_id,
                            training_date=training_date,
                            start_time=start_time,
                            end_time=end_time,
                            location=location,
                            name=name
                        )
                    )
                    loop.close()

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'result': result}).encode())
                except Exception as e:
                    logger.error(f"Ошибка при создании опроса: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())

            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        elif self.path == '/api/delete_poll':
            # Удаляем опрос в Telegram
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Проверяем авторизацию
            api_key = self.headers.get('X-API-Key', '')
            expected_key = os.getenv('BOT_API_KEY', 'volleybot_secret_key')

            if api_key != expected_key:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
                return

            try:
                chat_id = data.get('chat_id')
                message_id = data.get('message_id')
                action = data.get('action', 'stop')  # 'stop' или 'delete'

                if not all([chat_id, message_id]):
                    raise ValueError("Missing required fields")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        delete_poll_via_bot(
                            chat_id=chat_id,
                            message_id=message_id,
                            action=action
                        )
                    )
                    loop.close()

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'result': result}).encode())
                except Exception as e:
                    logger.error(f"Ошибка при удалении опроса: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())

            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def log_message(self, format, *args):
        """Логирование HTTP запросов"""
        logger.info(f"HTTP API: {args[0]}")


async def create_poll_via_bot(chat_id: str, training_date: str, start_time: str,
                               end_time: str, location: str, name: str,
                               topic_id: Optional[int] = None):
    """Создание опроса через бота (вызывается из веб-сервера)"""
    from utils import format_date_with_weekday
    import uuid

    # Форматируем дату
    date_obj = datetime.strptime(training_date, '%Y-%m-%d')
    formatted_date = format_date_with_weekday(date_obj)

    # Формируем вопрос
    question = f"{name} {formatted_date} {start_time} - {end_time} {location}"

    # Варианты ответов
    options = ['Буду', 'Не буду', 'Возможно']

    # Создаём бота и отправляем опрос
    from telegram import Bot
    bot = Bot(token=volley_bot.bot_token)

    try:
        data = {
            'chat_id': chat_id,
            'question': question,
            'options': json.dumps(options, ensure_ascii=False),
            'is_anonymous': False,
            'allows_multiple_answers': False
        }
        if topic_id is not None:
            data['message_thread_id'] = topic_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'https://api.telegram.org/bot{volley_bot.bot_token}/sendPoll',
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if result.get('ok'):
                message_id = result['result']['message_id']

                # Сохраняем опрос в БД с полной информацией
                poll_id = str(uuid.uuid4())
                volley_bot.db.add_active_poll(
                    poll_id=poll_id,
                    chat_id=chat_id,
                    message_id=message_id,
                    message_thread_id=topic_id,
                    template_id='scheduled',
                    name=name,
                    training_date=training_date,
                    training_time=f'{start_time} - {end_time}',
                    location=location
                )

                logger.info(f"Создан опрос в чате {chat_id}{' (топик ' + str(topic_id) + ')' if topic_id else ''}")
                return {'success': True, 'message_id': message_id, 'poll_id': poll_id}
            else:
                raise Exception(f"Telegram API error: {result}")
    finally:
        await bot.close()


async def delete_poll_via_bot(chat_id: str, message_id: int, action: str = 'stop'):
    """
    Удаление/остановка опроса в Telegram (вызывается из веб-сервера)
    
    Args:
        chat_id: ID чата
        message_id: ID сообщения с опросом
        action: 'stop' - остановить голосование, 'delete' - удалить сообщение
    """
    from telegram import Bot
    bot = Bot(token=volley_bot.bot_token)

    try:
        async with httpx.AsyncClient() as client:
            if action == 'delete':
                # Полное удаление сообщения
                response = await client.post(
                    f'https://api.telegram.org/bot{volley_bot.bot_token}/deleteMessage',
                    json={
                        'chat_id': chat_id,
                        'message_id': message_id
                    },
                    timeout=30
                )
            else:
                # Остановка голосования
                response = await client.post(
                    f'https://api.telegram.org/bot{volley_bot.bot_token}/stopPoll',
                    json={
                        'chat_id': chat_id,
                        'message_id': message_id
                    },
                    timeout=30
                )
            
            response.raise_for_status()
            result = response.json()

            if result.get('ok'):
                if action == 'delete':
                    logger.info(f"Опрос удалён из чата {chat_id}")
                    return {'success': True, 'message': 'Poll deleted'}
                else:
                    logger.info(f"Опрос остановлен в чате {chat_id}")
                    return {'success': True, 'message': 'Poll stopped'}
            else:
                raise Exception(f"Telegram API error: {result}")
    finally:
        await bot.close()


def start_http_server(port=8001):
    """Запуск HTTP сервера для API бота"""
    server = HTTPServer(('127.0.0.1', port), BotAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"HTTP API сервер запущен на порту {port}")
    return server


# ==================== Основная функция ====================

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(volley_bot.bot_token).build()

    # Сохраняем экземпляр бота в context.bot_data
    application.bot_data['volley_bot'] = volley_bot

    # Запускаем HTTP сервер для API
    start_http_server(port=8001)

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getid", get_user_id))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    logger.info("Запуск бота...")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
