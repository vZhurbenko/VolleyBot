#!/usr/bin/env python3
"""
Volleyball Poll Bot - продвинутый Telegram-бот для управления опросами о посещении волейбольных тренировок
"""

import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отключаем избыточное логирование httpx (Telegram API запросы)
logging.getLogger('httpx').setLevel(logging.WARNING)


class VolleyBot:
    """
    Основной класс бота для управления опросами волейбольных тренировок
    """

    def __init__(self, token_file: str = ".bot_token", db_path: str = "volleybot.db"):
        self.token_file = token_file
        self.bot_token = self.load_bot_token(token_file)

        # Инициализация базы данных
        self.db = Database(db_path)

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

        # Флаг для режима ожидания ID админа
        self.waiting_for_admin_id = False
        self.pending_user_id = None

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
            # Для расписания возвращаем дефолтный шаблон
            default_template = self.get_default_template()
            if default_template:
                template_copy = default_template.copy()
                template_copy['id'] = 'scheduled'
                return template_copy
        elif template_id == 'single':
            # Для одиночного опроса возвращаем дефолтный шаблон
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
            # Возвращаем копию шаблона с фиктивным ID для совместимости
            template_copy = default_template.copy()
            template_copy['id'] = 'default'
            return [template_copy]
        return []
    
    async def get_next_occurrence(self, day_of_week: str, time_str: str) -> datetime:
        """Вычисление следующего occurrence события"""
        # Преобразуем день недели в числовой формат (0-6, где 0 - понедельник)
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_day = days_map.get(day_of_week.lower())
        if target_day is None:
            raise ValueError(f"Неверный день недели: {day_of_week}")
        
        # Разбираем время
        hour, minute = map(int, time_str.split(':'))
        
        # Получаем текущую дату и время
        now = datetime.now()
        
        # Вычисляем дату следующего occurrence
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_date = now + timedelta(days=days_ahead)
        next_datetime = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_datetime
    
    async def get_next_sunday(self) -> str:
        """Вычисление даты следующего воскресенья"""
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7  # 6 - воскресенье
        if days_until_sunday == 0:  # Если сегодня воскресенье
            next_sunday = today + timedelta(days=7)
        else:
            next_sunday = today + timedelta(days=days_until_sunday)
        return next_sunday.strftime('%d.%m.%Y')
    
    async def create_poll(self, bot: Bot, chat_id: str, question: str, options: List[str], 
                         is_anonymous: bool = False, message_thread_id: Optional[int] = None) -> Optional[Message]:
        """Создание опроса в указанном чате или топике"""
        try:
            kwargs = {
                'chat_id': chat_id,
                'question': question,
                'options': options,
                'is_anonymous': is_anonymous,
                'allows_multiple_answers': False
            }
            
            # Если указан message_thread_id, добавляем его в параметры
            if message_thread_id is not None:
                kwargs['message_thread_id'] = message_thread_id
            
            message = await bot.send_poll(**kwargs)
            return message
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
            # Перезапускаем опрос, так как stop_poll закрывает его
            # Для получения результатов без закрытия нужно использовать другие методы
            # В данном случае мы просто возвращаем объект опроса
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
        
        # Вычисляем дату тренировки на основе дня тренировки в шаблоне
        training_day = template['training_day']
        training_time = template['training_time']
        
        # Получаем следующую дату для указанного дня недели
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_day = days_map.get(training_day.lower())
        if target_day is None:
            logger.error(f"Неверный день недели: {training_day}")
            return None
        
        # Вычисляем дату следующего occurrence
        now = datetime.now()
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_training_date = now + timedelta(days=days_ahead)
        formatted_date = next_training_date.strftime('%d.%m.%Y')
        
        # Подставляем дату и время в описание
        description = template['description'].replace('{date}', formatted_date).replace('{time}', training_time)
        
        # Создаем опрос
        poll_message = await self.create_poll(
            bot=bot,
            chat_id=chat_id,
            question=description,
            options=template['options'],
            is_anonymous=False,  # Опросы не анонимные
            message_thread_id=message_thread_id
        )
        
        if poll_message:
            # Закрепляем опрос
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
        """Создание опросов для дефолтного шаблона и всех расписаний"""
        template = self.get_default_template()
        if template.get('enabled', True):
            # Проверяем, совпадает ли сегодняшний день с днем создания опроса
            poll_day = template.get('poll_day', 'sunday')
            
            days_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            target_day = days_map.get(poll_day.lower())
            if target_day is not None and target_day == datetime.now().weekday():
                # Создаем опрос с использованием значений по умолчанию
                default_chat_id = template.get('default_chat_id')
                default_topic_id = template.get('default_topic_id')
                if default_chat_id:
                    await self.create_poll_from_template(bot, default_chat_id, default_topic_id)
        
        # Создаем опросы для всех расписаний
        schedules = self.get_poll_schedules()
        for schedule in schedules:
            if schedule.get('enabled', True):
                # Проверяем, совпадает ли сегодняшний день с днем создания опроса для этого расписания
                poll_day = schedule.get('poll_day', 'sunday')
                
                days_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                
                target_day = days_map.get(poll_day.lower())
                if target_day is not None and target_day == datetime.now().weekday():
                    # Создаем опрос с параметрами из расписания
                    await self.create_poll_from_schedule(bot, schedule)
    
    async def create_poll_from_schedule(self, bot: Bot, schedule: Dict[str, Any]):
        """Создание опроса из расписания"""
        # Используем параметры из расписания
        chat_id = schedule['chat_id']
        thread_id = schedule.get('message_thread_id', None)
        training_day = schedule['training_day']
        poll_day = schedule['poll_day']
        training_time = schedule['training_time']
        options = schedule.get('options', [])
        
        # Получаем следующую дату для указанного дня тренировки
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_day = days_map.get(training_day.lower())
        if target_day is None:
            logger.error(f"Неверный день недели: {training_day}")
            return None
        
        # Вычисляем дату следующего occurrence
        now = datetime.now()
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_training_date = now + timedelta(days=days_ahead)
        formatted_date = next_training_date.strftime('%d.%m.%Y')
        
        # Получаем описание из шаблона и подставляем дату и время
        template = self.get_default_template()
        description = template['description'].replace('{date}', formatted_date).replace('{time}', training_time)
        
        # Если в расписании есть свои варианты ответа, используем их
        if options:
            poll_options = options
        else:
            poll_options = template['options']
        
        # Создаем опрос
        poll_message = await self.create_poll(
            bot=bot,
            chat_id=chat_id,
            question=description,
            options=poll_options,
            is_anonymous=False,  # Опросы не анонимные
            message_thread_id=thread_id
        )
        
        if poll_message:
            # Закрепляем опрос
            await self.pin_message(bot, chat_id, poll_message.message_id)

            logger.info(f"Опрос создан из расписания {schedule['id']} в чате {chat_id}")

        return poll_message


# Экземпляр бота
volley_bot = VolleyBot(db_path="volleybot.db")


# Словарь для хранения состояния создания шаблона для каждого пользователя
creation_states = {}

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /getid - получить ID пользователя"""
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_info = f"Ваш ID: {user_id}\n"
    user_info += f"Имя: {first_name}\n"
    if username:
        user_info += f"Username: @{username}"

    await update.message.reply_text(user_info)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений для создания шаблонов"""
    user_id = update.effective_user.id
    
    # Проверяем, является ли пользователь администратором
    if user_id not in volley_bot.admin_user_ids:
        return  # Игнорируем сообщения от неадминистраторов
    
    # Проверяем, находится ли пользователь в процессе создания опроса
    if user_id in creation_states:
        state = creation_states[user_id]
        message_text = update.message.text.strip()

        if state['step'] == 'changing_name':
            # Изменение названия шаблона
            template = volley_bot.get_default_template()
            template['name'] = message_text
            volley_bot.update_default_template(template)
            
            await update.message.reply_text(f"Название шаблона изменено на: {message_text}")
            
            # Удаляем состояние пользователя
            user_id = update.effective_user.id
            if user_id in creation_states:
                del creation_states[user_id]
                
        elif state['step'] == 'changing_description':
            # Изменение описания шаблона
            template = volley_bot.get_default_template()
            template['description'] = message_text
            volley_bot.update_default_template(template)
            
            await update.message.reply_text(f"Описание шаблона изменено на: {message_text}")
            
            # Удаляем состояние пользователя
            user_id = update.effective_user.id
            if user_id in creation_states:
                del creation_states[user_id]
                
        elif state['step'] == 'changing_training_time':
            # Изменение времени тренировки
            template = volley_bot.get_default_template()
            template['training_time'] = message_text
            volley_bot.update_default_template(template)
            
            await update.message.reply_text(f"Время тренировки изменено на: {message_text}")
            
            # Удаляем состояние пользователя
            user_id = update.effective_user.id
            if user_id in creation_states:
                del creation_states[user_id]
                
        elif state['step'] == 'changing_options':
            # Изменение вариантов ответа
            options = [opt.strip() for opt in message_text.split('\n') if opt.strip()]
            if len(options) < 2:
                await update.message.reply_text("Пожалуйста, введите хотя бы 2 варианта ответа, каждый на новой строке.")
                return

            template = volley_bot.get_default_template()
            template['options'] = options
            volley_bot.update_default_template(template)

            await update.message.reply_text(f"Варианты ответа изменены. Теперь их {len(options)}.")

            # Удаляем состояние пользователя
            user_id = update.effective_user.id
            if user_id in creation_states:
                del creation_states[user_id]

        elif state['step'] == 'waiting_admin_id':
            # Добавление нового администратора по ID
            try:
                new_admin_id = int(message_text)
                volley_bot.db.add_admin_id(new_admin_id)
                volley_bot.admin_user_ids = volley_bot.db.get_admin_ids()
                await update.message.reply_text(
                    f"✅ Пользователь с ID {new_admin_id} успешно добавлен в администраторы!\n\n"
                    f"Всего администраторов: {len(volley_bot.admin_user_ids)}"
                )
                logger.info(f"Администратор {new_admin_id} добавлен пользователем {user_id}")
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID. Пожалуйста, введите числовое значение ID.")
            
            # Удаляем состояние пользователя
            if user_id in creation_states:
                del creation_states[user_id]

        elif state['step'] == 'waiting_training_time_input':
            # Сохраняем время тренировки и создаем опрос с указанными параметрами
            training_time = message_text
            chat_id = state['chat_id']
            thread_id = state['thread_id']
            training_day = state['training_day']
            poll_day = state['poll_day']

            # Спрашиваем, нужно ли создать расписание для регулярного создания опросов
            user_id = update.effective_user.id
            creation_states[user_id] = {
                'step': 'waiting_schedule_confirmation',
                'chat_id': chat_id,
                'thread_id': thread_id,
                'training_day': training_day,
                'poll_day': poll_day,
                'training_time': training_time
            }

            # Предлагаем создать расписание
            keyboard = [
                [InlineKeyboardButton("✅ Создать расписание", callback_data='create_schedule_yes')],
                [InlineKeyboardButton("❌ Только один раз", callback_data='create_schedule_no')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Будем создавать опрос регулярно?\n\n"
                f"Тренировка: {training_day} в {training_time}\n"
                f"Опрос создается: {poll_day}\n"
                f"Чат: {chat_id}" + (f" (топик {thread_id})" if thread_id else ""),
                reply_markup=reply_markup
            )

        elif state['step'] == 'schedule_changing_time':
            # Изменение времени тренировки в расписании
            schedule_id = state['schedule_id']
            new_time = message_text
            
            schedules = volley_bot.get_poll_schedules()
            for schedule in schedules:
                if schedule['id'] == schedule_id:
                    schedule['training_time'] = new_time
                    volley_bot.save_config()
                    break
            
            await update.message.reply_text(
                f"✅ Время тренировки изменено на {new_time}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_schedule:{schedule_id}")]])
            )
            
            # Удаляем состояние
            del creation_states[user_id]

        elif state['step'] == 'schedule_changing_poll_time':
            # Изменение времени отправки опроса в расписании
            schedule_id = state['schedule_id']
            new_time = message_text

            schedules = volley_bot.get_poll_schedules()
            for schedule in schedules:
                if schedule['id'] == schedule_id:
                    schedule['poll_time'] = new_time
                    volley_bot.save_config()
                    break

            await update.message.reply_text(
                f"✅ Время отправки опроса изменено на {new_time} (MSK)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_schedule:{schedule_id}")]])
            )

            # Удаляем состояние
            del creation_states[user_id]

        elif state['step'] == 'waiting_options':
            # Сохраняем варианты ответов
            options = [opt.strip() for opt in message_text.split('\n') if opt.strip()]
            if len(options) < 2:
                await update.message.reply_text("Пожалуйста, введите хотя бы 2 варианта ответа, каждый на новой строке.")
                return
                
            state['options'] = options
            state['step'] = 'confirm_creation'
            
            # Показываем сводку и предлагаем подтвердить
            summary = (
                f"Новый шаблон опроса:\n\n"
                f"Название: {state['name']}\n"
                f"Описание: {state['description']}\n"
                f"Чат: {state['chat_id']}\n"
                f"День тренировки: {state['training_day']}\n"
                f"Время тренировки: {state['training_time']}\n"
                f"День опроса: {state['poll_day']}\n"
                f"Варианты ответа:\n"
            )
            for i, option in enumerate(options, 1):
                summary += f"{i}. {option}\n"
            
            keyboard = [
                [InlineKeyboardButton("✅ Создать", callback_data="confirm_create_template")],
                [InlineKeyboardButton("❌ Отменить", callback_data="cancel_create_template")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(summary, reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    # Проверяем, является ли пользователь администратором
    user_id = update.effective_user.id
    if user_id not in volley_bot.admin_user_ids:
        await update.message.reply_text('❌ У вас нет прав для управления этим ботом.')
        return

    keyboard = [
        [
            InlineKeyboardButton("📊 Создать опрос", callback_data='create_poll_menu'),
        ],
        [
            InlineKeyboardButton("📋 Список опросов", callback_data='polls_list_menu'),
            InlineKeyboardButton("✏️ Редактировать шаблон", callback_data='edit_poll_menu')
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data='settings_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        '🏐 Привет! Это бот для управления опросами о волейбольных тренировках.\n\n'
        'Выберите действие:',
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()
    
    # Проверяем, является ли пользователь администратором
    user_id = update.effective_user.id
    if user_id not in volley_bot.admin_user_ids:
        await query.answer(text='❌ У вас нет прав для управления этим ботом.', show_alert=True)
        return
    
    if query.data == 'create_poll_menu':
        # Предлагаем пользователю выбор: использовать значения по умолчанию или ввести вручную
        template = volley_bot.get_default_template()
        default_chat_id = template.get('default_chat_id', '')
        default_topic_id = template.get('default_topic_id', None)
        
        keyboard = []
        
        # Если нет значений по умолчанию, предлагаем их настроить
        if not default_chat_id:
            await query.edit_message_text(
                text="❌ Не задан чат по умолчанию в шаблоне.\n\n"
                     "Настройте шаблон опроса в разделе '✏️ Редактировать шаблон'",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]])
            )
            return

        # Формируем текст с информацией о значениях по умолчанию
        info_text = f"📍 Чат: {default_chat_id}\n"
        if default_topic_id:
            info_text += f"📍 Топик: {default_topic_id}\n"

        keyboard.append([InlineKeyboardButton("🚀 Создать опрос", callback_data='create_with_defaults')])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"Значения по умолчанию:\n{info_text}\n\nНажмите кнопку ниже для создания опроса:",
            reply_markup=reply_markup
        )
        
    elif query.data == 'create_with_defaults':
        # Запрашиваем дни недели и время для создания опроса с использованием значений по умолчанию
        template = volley_bot.get_default_template()
        default_chat_id = template.get('default_chat_id', '')
        
        if not default_chat_id:
            await query.edit_message_text(
                text="❌ Не задан чат по умолчанию в шаблоне.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
            )
            return
        
        # Сохраняем состояние пользователя для ожидания дня тренировки
        user_id = update.effective_user.id
        default_topic_id = template.get('default_topic_id', None)
        creation_states[user_id] = {
            'step': 'waiting_training_day',
            'chat_id': default_chat_id,
            'thread_id': default_topic_id
        }

        # Предлагаем выбор дня тренировки
        keyboard = [
            [InlineKeyboardButton("Понедельник", callback_data="selected_day:monday")],
            [InlineKeyboardButton("Вторник", callback_data="selected_day:tuesday")],
            [InlineKeyboardButton("Среда", callback_data="selected_day:wednesday")],
            [InlineKeyboardButton("Четверг", callback_data="selected_day:thursday")],
            [InlineKeyboardButton("Пятница", callback_data="selected_day:friday")],
            [InlineKeyboardButton("Суббота", callback_data="selected_day:saturday")],
            [InlineKeyboardButton("Воскресенье", callback_data="selected_day:sunday")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="Выберите день недели, в который будет тренировка:",
            reply_markup=reply_markup
        )

    elif query.data.startswith('create_poll:'):
        # Создаем опрос из дефолтного шаблона в указанный чат
        parts = query.data.split(':')
        if len(parts) >= 2:
            target_chat_id = parts[1]
        else:
            await query.edit_message_text(
                text="❌ Неверный формат данных.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
            )
            return

        # Создаем опрос из дефолтного шаблона
        poll_message = await volley_bot.create_poll_from_template(context.bot, target_chat_id)

        if poll_message:
            await query.edit_message_text(text=f"✅ Опрос успешно создан и закреплен в чате {target_chat_id}!")
        else:
            await query.edit_message_text(text=f"❌ Ошибка при создании опроса в чате {target_chat_id}.")

        # Возвращаемся к главному меню
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    elif query.data == 'polls_list_menu':
        # Показ списка всех расписаний опросов
        schedules = volley_bot.get_poll_schedules()

        if not schedules:
            await query.edit_message_text(
                text="❌ Нет активных расписаний опросов.\n\n"
                     "Нажмите '📊 Создать опрос', чтобы добавить новое расписание.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]])
            )
            return

        keyboard = []
        for schedule in schedules:
            status = "✅ Вкл" if schedule.get('enabled', True) else "❌ Выкл"
            keyboard.append([
                InlineKeyboardButton(
                    f"📋 {schedule['name']} ({status})",
                    callback_data=f"edit_schedule:{schedule['id']}"
                )
            ])

        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="📋 Список расписаний опросов:\n\n"
                 "Выберите опрос для редактирования настроек:",
            reply_markup=reply_markup
        )

    elif query.data.startswith('edit_schedule:'):
        # Редактирование выбранного расписания
        schedule_id = query.data.split(':')[1]
        schedules = volley_bot.get_poll_schedules()
        schedule = None
        for s in schedules:
            if s['id'] == schedule_id:
                schedule = s
                break

        if not schedule:
            await query.edit_message_text(
                text="❌ Расписание не найдено!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='polls_list_menu')]])
            )
            return

        status = "✅ Включено" if schedule.get('enabled', True) else "❌ Отключено"
        template = volley_bot.get_default_template()
        options_text = '\n'.join([f"  • {opt}" for opt in template.get('options', [])]) if template else "Не заданы"
        poll_time = schedule.get('poll_time', '12:00')

        info = (
            f"📋 **{schedule['name']}**\n\n"
            f"Статус: {status}\n"
            f"День тренировки: {schedule['training_day']}\n"
            f"Время тренировки: {schedule['training_time']}\n"
            f"День отправки опроса: {schedule['poll_day']}\n"
            f"Время отправки опроса: {poll_time} (MSK)\n"
            f"Чат: {schedule['chat_id']}\n"
            f"Топик: {schedule.get('message_thread_id', 'Нет')}\n\n"
            f"Варианты ответа:\n{options_text}"
        )

        keyboard = [
            [InlineKeyboardButton("✏️ День тренировки", callback_data=f"schedule_edit_training_day:{schedule_id}")],
            [InlineKeyboardButton("✏️ Время тренировки", callback_data=f"schedule_edit_training_time:{schedule_id}")],
            [InlineKeyboardButton("✏️ День отправки", callback_data=f"schedule_edit_poll_day:{schedule_id}")],
            [InlineKeyboardButton("✏️ Время отправки", callback_data=f"schedule_edit_poll_time:{schedule_id}")],
            [InlineKeyboardButton("🔄 Вкл/Выкл", callback_data=f"schedule_toggle_enabled:{schedule_id}")],
            [InlineKeyboardButton("🗑️ Удалить расписание", callback_data=f"schedule_delete:{schedule_id}")],
            [InlineKeyboardButton("◀️ Назад", callback_data='polls_list_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=info, reply_markup=reply_markup)

    elif query.data.startswith('schedule_edit_training_day:'):
        # Изменение дня тренировки в расписании
        schedule_id = query.data.split(':')[1]
        
        keyboard = [
            [InlineKeyboardButton("Понедельник", callback_data=f"schedule_set_training_day:{schedule_id}:monday")],
            [InlineKeyboardButton("Вторник", callback_data=f"schedule_set_training_day:{schedule_id}:tuesday")],
            [InlineKeyboardButton("Среда", callback_data=f"schedule_set_training_day:{schedule_id}:wednesday")],
            [InlineKeyboardButton("Четверг", callback_data=f"schedule_set_training_day:{schedule_id}:thursday")],
            [InlineKeyboardButton("Пятница", callback_data=f"schedule_set_training_day:{schedule_id}:friday")],
            [InlineKeyboardButton("Суббота", callback_data=f"schedule_set_training_day:{schedule_id}:saturday")],
            [InlineKeyboardButton("Воскресенье", callback_data=f"schedule_set_training_day:{schedule_id}:sunday")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="Выберите новый день тренировки:",
            reply_markup=reply_markup
        )

    elif query.data.startswith('schedule_set_training_day:'):
        # Установка дня тренировки
        parts = query.data.split(':')
        schedule_id = parts[1]
        new_day = parts[2]
        
        schedules = volley_bot.get_poll_schedules()
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule['training_day'] = new_day
                # Обновляем название расписания
                schedule['name'] = f"Расписание {new_day}->{schedule['poll_day']}"
                volley_bot.save_config()
                break

        await query.edit_message_text(
            text=f"✅ День тренировки изменен на {new_day}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_schedule:{schedule_id}")]])
        )

    elif query.data.startswith('schedule_edit_training_time:'):
        # Изменение времени тренировки в расписании
        schedule_id = query.data.split(':')[1]
        
        # Сохраняем ID расписания в состоянии пользователя
        user_id = update.effective_user.id
        creation_states[user_id] = {
            'step': 'schedule_changing_time',
            'schedule_id': schedule_id
        }

        await query.edit_message_text(
            text="Введите новое время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_schedule:{schedule_id}")]])
        )

    elif query.data.startswith('schedule_edit_poll_day:'):
        # Изменение дня отправки опроса в расписании
        schedule_id = query.data.split(':')[1]
        
        keyboard = [
            [InlineKeyboardButton("Понедельник", callback_data=f"schedule_set_poll_day:{schedule_id}:monday")],
            [InlineKeyboardButton("Вторник", callback_data=f"schedule_set_poll_day:{schedule_id}:tuesday")],
            [InlineKeyboardButton("Среда", callback_data=f"schedule_set_poll_day:{schedule_id}:wednesday")],
            [InlineKeyboardButton("Четверг", callback_data=f"schedule_set_poll_day:{schedule_id}:thursday")],
            [InlineKeyboardButton("Пятница", callback_data=f"schedule_set_poll_day:{schedule_id}:friday")],
            [InlineKeyboardButton("Суббота", callback_data=f"schedule_set_poll_day:{schedule_id}:saturday")],
            [InlineKeyboardButton("Воскресенье", callback_data=f"schedule_set_poll_day:{schedule_id}:sunday")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text="Выберите новый день отправки опроса:",
            reply_markup=reply_markup
        )

    elif query.data.startswith('schedule_set_poll_day:'):
        # Установка дня отправки опроса
        parts = query.data.split(':')
        schedule_id = parts[1]
        new_day = parts[2]
        
        schedules = volley_bot.get_poll_schedules()
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule['poll_day'] = new_day
                # Обновляем название расписания
                training_day = schedule['training_day']
                schedule['name'] = f"Расписание {training_day}->{new_day}"
                volley_bot.save_config()
                break

        await query.edit_message_text(
            text=f"✅ День отправки опроса изменен на {new_day}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_schedule:{schedule_id}")]])
        )

    elif query.data.startswith('schedule_edit_poll_time:'):
        # Изменение времени отправки опроса в расписании
        schedule_id = query.data.split(':')[1]
        
        # Сохраняем ID расписания в состоянии пользователя
        user_id = update.effective_user.id
        creation_states[user_id] = {
            'step': 'schedule_changing_poll_time',
            'schedule_id': schedule_id
        }
        
        await query.edit_message_text(
            text="Введите новое время отправки опроса в формате ЧЧ:ММ (например, 12:00):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_schedule:{schedule_id}")]])
        )

    elif query.data.startswith('schedule_toggle_enabled:'):
        # Включение/выключение расписания
        schedule_id = query.data.split(':')[1]
        
        schedules = volley_bot.get_poll_schedules()
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule['enabled'] = not schedule.get('enabled', True)
                volley_bot.save_config()
                status = "включено" if schedule['enabled'] else "выключено"
                await query.edit_message_text(
                    text=f"✅ Расписание {status}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"edit_schedule:{schedule_id}")]])
                )
                break

    elif query.data.startswith('schedule_delete:'):
        # Удаление расписания
        schedule_id = query.data.split(':')[1]
        
        # Удаляем расписание
        volley_bot.remove_poll_schedule(schedule_id)
        
        await query.edit_message_text(
            text="✅ Расписание успешно удалено!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='polls_list_menu')]])
        )

    elif query.data == 'edit_poll_menu':
        # Меню редактирования дефолтного шаблона
        template = volley_bot.get_default_template()
        keyboard = []
        
        if template:
            keyboard.append([
                InlineKeyboardButton(
                    template['name'], 
                    callback_data="edit_default_template"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("✏️ Редактировать шаблон", callback_data="edit_default_template")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if template:
            info = (
                f"Текущий шаблон:\n"
                f"Название: {template['name']}\n"
                f"Описание: {template['description']}\n"
                f"День тренировки: {template['training_day']}\n"
                f"День опроса: {template['poll_day']}\n"
                f"Время тренировки: {template['training_time']}\n"
                f"Включено: {'Да' if template['enabled'] else 'Нет'}\n\n"
                f"Варианты ответа:\n"
            )
            
            for i, option in enumerate(template['options'], 1):
                info += f"{i}. {option}\n"
        else:
            info = "Шаблон не найден!"
        
        await query.edit_message_text(
            text=info,
            reply_markup=reply_markup
        )
        
    elif query.data == 'edit_default_template':
        # Редактирование дефолтного шаблона
        template = volley_bot.get_default_template()
        
        if template:
            info = (
                f"Редактирование шаблона:\n"
                f"Название: {template['name']}\n"
                f"Описание: {template['description']}\n"
                f"День тренировки: {template['training_day']}\n"
                f"День опроса: {template['poll_day']}\n"
                f"Время тренировки: {template['training_time']}\n"
                f"Включено: {'Да' if template['enabled'] else 'Нет'}\n\n"
                f"Варианты ответа:\n"
            )
            
            for i, option in enumerate(template['options'], 1):
                info += f"{i}. {option}\n"
        else:
            info = "Шаблон не найден!"
        
        keyboard = [
            [InlineKeyboardButton("✏️ Изменить название", callback_data='change_name')],
            [InlineKeyboardButton("✏️ Изменить описание", callback_data='change_description')],
            [InlineKeyboardButton("✏️ Изменить день тренировки", callback_data='change_training_day')],
            [InlineKeyboardButton("✏️ Изменить день опроса", callback_data='change_poll_day')],
            [InlineKeyboardButton("✏️ Изменить время тренировки", callback_data='change_training_time')],
            [InlineKeyboardButton("✏️ Изменить варианты", callback_data='change_options')],
            [InlineKeyboardButton("◀️ Назад", callback_data='edit_poll_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text=info, reply_markup=reply_markup)
        
    elif query.data == 'change_name':
        # Изменение названия шаблона
        user_id = update.effective_user.id
        creation_states[user_id] = {'step': 'changing_name'}
        await query.edit_message_text(
            text="Введите новое название шаблона:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
        )
        
    elif query.data == 'change_description':
        # Изменение описания шаблона
        user_id = update.effective_user.id
        creation_states[user_id] = {'step': 'changing_description'}
        await query.edit_message_text(
            text="Введите новое описание шаблона (используйте {date} и {time}):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
        )
        
    elif query.data == 'change_training_day':
        # Изменение дня тренировки
        user_id = update.effective_user.id
        creation_states[user_id] = {'step': 'changing_training_day'}
        
        # Предлагаем выбор дня тренировки
        keyboard = [
            [InlineKeyboardButton("Понедельник", callback_data="selected_day:monday")],
            [InlineKeyboardButton("Вторник", callback_data="selected_day:tuesday")],
            [InlineKeyboardButton("Среда", callback_data="selected_day:wednesday")],
            [InlineKeyboardButton("Четверг", callback_data="selected_day:thursday")],
            [InlineKeyboardButton("Пятница", callback_data="selected_day:friday")],
            [InlineKeyboardButton("Суббота", callback_data="selected_day:saturday")],
            [InlineKeyboardButton("Воскресенье", callback_data="selected_day:sunday")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="Выберите день недели, в который будет тренировка:",
            reply_markup=reply_markup
        )
        
    elif query.data == 'change_poll_day':
        # Изменение дня опроса
        user_id = update.effective_user.id
        creation_states[user_id] = {'step': 'changing_poll_day'}
        
        # Предлагаем выбор дня для создания опроса
        keyboard = [
            [InlineKeyboardButton("Понедельник", callback_data="selected_poll_day:monday")],
            [InlineKeyboardButton("Вторник", callback_data="selected_poll_day:tuesday")],
            [InlineKeyboardButton("Среда", callback_data="selected_poll_day:wednesday")],
            [InlineKeyboardButton("Четверг", callback_data="selected_poll_day:thursday")],
            [InlineKeyboardButton("Пятница", callback_data="selected_poll_day:friday")],
            [InlineKeyboardButton("Суббота", callback_data="selected_poll_day:saturday")],
            [InlineKeyboardButton("Воскресенье", callback_data="selected_poll_day:sunday")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="Выберите день недели, в который бот должен создавать опрос:",
            reply_markup=reply_markup
        )
        
    elif query.data == 'change_training_time':
        # Изменение времени тренировки
        user_id = update.effective_user.id
        creation_states[user_id] = {'step': 'changing_training_time'}
        await query.edit_message_text(
            text="Введите время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
        )
        
    elif query.data == 'change_options':
        # Изменение вариантов ответа
        user_id = update.effective_user.id
        creation_states[user_id] = {'step': 'changing_options'}
        await query.edit_message_text(
            text="Введите варианты ответов, каждый на новой строке:\n\n"
                 "Пример:\n"
                 "Буду\n"
                 "Не буду\n"
                 "Возможно",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
        )
        
    elif query.data.startswith('selected_day:'):
        # Обработка выбора дня - зависит от текущего состояния пользователя
        user_id = update.effective_user.id
        selected_day = query.data.split(':')[1]
        
        if user_id in creation_states:
            state = creation_states[user_id]
            if state['step'] == 'waiting_training_day':
                # Выбран день тренировки, теперь запрашиваем день создания опроса
                creation_states[user_id] = {
                    'step': 'waiting_poll_day',
                    'chat_id': state['chat_id'],
                    'thread_id': state['thread_id'],
                    'training_day': selected_day
                }

                # Предлагаем выбор дня для создания опроса
                keyboard = [
                    [InlineKeyboardButton("Понедельник", callback_data="poll_day_selection:monday")],
                    [InlineKeyboardButton("Вторник", callback_data="poll_day_selection:tuesday")],
                    [InlineKeyboardButton("Среда", callback_data="poll_day_selection:wednesday")],
                    [InlineKeyboardButton("Четверг", callback_data="poll_day_selection:thursday")],
                    [InlineKeyboardButton("Пятница", callback_data="poll_day_selection:friday")],
                    [InlineKeyboardButton("Суббота", callback_data="poll_day_selection:saturday")],
                    [InlineKeyboardButton("Воскресенье", callback_data="poll_day_selection:sunday")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    text="Выберите день недели, в который бот должен создать опрос:",
                    reply_markup=reply_markup
                )
            else:
                await query.answer(text="Ошибка: неверное состояние", show_alert=True)
        else:
            # Обработка для редактирования шаблона (старая логика)
            # Обновляем шаблон
            template = volley_bot.get_default_template()
            template['training_day'] = selected_day
            volley_bot.update_default_template(template)
            
            await query.edit_message_text(
                text=f"День тренировки изменен на {selected_day}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
            )
        
    elif query.data.startswith('selected_poll_day:'):
        # Выбор дня опроса
        user_id = update.effective_user.id
        selected_day = query.data.split(':')[1]
        
        # Обновляем шаблон
        template = volley_bot.get_default_template()
        template['poll_day'] = selected_day
        volley_bot.update_default_template(template)
        
        await query.edit_message_text(
            text=f"День опроса изменен на {selected_day}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
        )
        
    elif query.data.startswith('poll_day_selection:'):
        # Обработка выбора дня опроса при создании опроса
        user_id = update.effective_user.id
        selected_day = query.data.split(':')[1]
        
        if user_id in creation_states:
            state = creation_states[user_id]
            if state['step'] == 'waiting_poll_day':
                # Выбран день создания опроса, теперь запрашиваем время тренировки
                creation_states[user_id] = {
                    'step': 'waiting_training_time_input',
                    'chat_id': state['chat_id'],
                    'thread_id': state['thread_id'],
                    'training_day': state['training_day'],
                    'poll_day': selected_day
                }

                await query.edit_message_text(
                    text="Введите время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
                )
            else:
                await query.answer(text="Ошибка: неверное состояние", show_alert=True)
        else:
            # Обработка для редактирования шаблона (старая логика)
            # Обновляем шаблон
            template = volley_bot.get_default_template()
            template['poll_day'] = selected_day
            volley_bot.update_default_template(template)
            
            await query.edit_message_text(
                text=f"День опроса изменен на {selected_day}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
            )
            
    elif query.data == 'create_schedule_yes':
        # Создание расписания (без немедленной отправки опроса)
        user_id = update.effective_user.id
        if user_id in creation_states:
            state = creation_states[user_id]

            # Генерируем уникальный ID для расписания
            schedule_id = str(uuid.uuid4())

            # Создаем расписание
            schedule = {
                'id': schedule_id,
                'name': f"Расписание {state['training_day']}->{state['poll_day']}",
                'chat_id': state['chat_id'],
                'message_thread_id': state['thread_id'],
                'training_day': state['training_day'],
                'poll_day': state['poll_day'],
                'training_time': state['training_time'],
                'poll_time': '12:00',  # Время отправки опроса по умолчанию
                'enabled': True
            }

            # Добавляем расписание
            volley_bot.add_poll_schedule(schedule)

            await query.edit_message_text(
                text=f"✅ Расписание успешно создано!\n\n"
                     f"📋 Параметры:\n"
                     f"День тренировки: {state['training_day']}\n"
                     f"Время тренировки: {state['training_time']}\n"
                     f"День отправки опроса: {state['poll_day']}\n"
                     f"Время отправки опроса: 12:00 (MSK)\n"
                     f"Чат: {state['chat_id']}" + (f" (топик {state['thread_id']})" if state['thread_id'] else "") + "\n\n"
                     f"Опросы будут автоматически создаваться каждый {state['poll_day']} в 12:00 для тренировки в {state['training_day']}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='polls_list_menu')]])
            )

            # Удаляем состояние пользователя
            if user_id in creation_states:
                del creation_states[user_id]
        else:
            await query.answer(text="Ошибка: состояние не найдено", show_alert=True)

    elif query.data == 'create_schedule_no':
        # Создание только одного опроса без расписания
        user_id = update.effective_user.id
        if user_id in creation_states:
            state = creation_states[user_id]
            
            logger.info(f"create_schedule_no: state={state}")

            # Проверяем наличие всех необходимых данных
            required_fields = ['chat_id', 'training_day', 'poll_day', 'training_time']
            missing_fields = [f for f in required_fields if f not in state]
            
            if missing_fields:
                await query.edit_message_text(
                    text=f"❌ Ошибка: отсутствуют данные: {', '.join(missing_fields)}\n\n"
                         f"Начните создание опроса заново.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
                )
                del creation_states[user_id]
                return

            # Получаем следующую дату для указанного дня тренировки
            days_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }

            target_day = days_map.get(state['training_day'].lower())
            if target_day is None:
                await query.edit_message_text(
                    text=f"❌ Неверный день недели: {state['training_day']}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
                )
                return

            # Вычисляем дату следующего occurrence
            now = datetime.now()
            days_ahead = target_day - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7

            next_training_date = now + timedelta(days=days_ahead)
            formatted_date = next_training_date.strftime('%d.%m.%Y')

            # Получаем описание из шаблона и подставляем дату и время
            template = volley_bot.get_default_template()
            description = template['description'].replace('{date}', formatted_date).replace('{time}', state['training_time'])

            try:
                # Создаем опрос
                poll_message = await volley_bot.create_poll(
                    context.bot,
                    state['chat_id'],
                    description,
                    template['options'],
                    is_anonymous=False,  # Опросы не анонимные
                    message_thread_id=state['thread_id']
                )

                if poll_message:
                    # Закрепляем опрос
                    await volley_bot.pin_message(context.bot, state['chat_id'], poll_message.message_id)

                    await query.edit_message_text(
                        text=f"✅ Опрос успешно создан и закреплен в чате {state['chat_id']}{f' (топик {state['thread_id']})' if state['thread_id'] else ''}!\n\n"
                             f"Опрос создан единоразово, без автоматического повторения.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
                    )
                else:
                    await query.edit_message_text(
                        text=f"❌ Ошибка при создании опроса в чате {state['chat_id']}.",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
                    )
            except Exception as e:
                logger.error(f"Ошибка при создании одноразового опроса: {e}")
                await query.edit_message_text(
                    text=f"❌ Ошибка при создании опроса: {e}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
                )

            # Удаляем состояние пользователя
            if user_id in creation_states:
                del creation_states[user_id]
        else:
            await query.answer(text="Ошибка: состояние не найдено", show_alert=True)

    elif query.data.startswith('poll_day:'):
        # Обработка выбора дня - зависит от текущего состояния пользователя
        user_id = update.effective_user.id
        selected_day = query.data.split(':')[1]
        
        if user_id in creation_states:
            state = creation_states[user_id]
            if state['step'] == 'waiting_poll_day':
                # Выбран день создания опроса, теперь запрашиваем время тренировки
                creation_states[user_id]['poll_day'] = selected_day
                creation_states[user_id]['step'] = 'waiting_training_time_input'

                await query.edit_message_text(
                    text="Введите время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
                )
            else:
                await query.answer(text="Ошибка: неверное состояние", show_alert=True)
        else:
            # Обработка для редактирования шаблона (старая логика)
            # Обновляем шаблон
            template = volley_bot.get_default_template()
            template['poll_day'] = selected_day
            volley_bot.update_default_template(template)
            
            await query.edit_message_text(
                text=f"День опроса изменен на {selected_day}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_default_template')]])
            )
            
    elif query.data == 'confirm_create_template':
        # Подтверждение создания шаблона
        user_id = update.effective_user.id
        if user_id in creation_states:
            state = creation_states[user_id]
            
            # Генерируем уникальный ID для шаблона
            template_id = str(uuid.uuid4())
            
            # Создаем новый шаблон
            new_template = {
                'id': template_id,
                'name': state['name'],
                'description': state['description'],
                'chat_id': state['chat_id'],
                'training_day': state['training_day'],
                'poll_day': state['poll_day'],
                'training_time': state['training_time'],
                'options': state['options'],
                'enabled': True
            }
            
            # Добавляем шаблон в конфиг
            volley_bot.add_poll_template(new_template)
            
            # Удаляем состояние пользователя
            del creation_states[user_id]
            
            await query.edit_message_text(
                text=f"✅ Шаблон '{state['name']}' успешно создан!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_poll_menu')]])
            )
        else:
            await query.answer(text="Ошибка: состояние не найдено", show_alert=True)
            
    elif query.data == 'cancel_create_template':
        # Отмена создания шаблона
        user_id = update.effective_user.id
        if user_id in creation_states:
            del creation_states[user_id]
        
        await query.edit_message_text(
            text="❌ Создание шаблона отменено.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_poll_menu')]])
        )
        
    elif query.data == 'create_template_start':
        # Начало создания шаблона - сохраняем состояние пользователя
        user_id = update.effective_user.id
        creation_states[user_id] = {
            'step': 'waiting_name'
        }
        
        await query.edit_message_text(
            text="Введите название для нового шаблона опроса:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='edit_poll_menu')]])
        )
        
    elif query.data.startswith('create_poll:'):
        # Создаем опрос из выбранного шаблона в указанный чат
        parts = query.data.split(':')
        template_id = parts[1]
        target_chat_id = parts[2]
        
        # Получаем шаблон и изменяем chat_id на целевой
        template = volley_bot.get_poll_template_by_id(template_id)
        if not template:
            await query.edit_message_text(
                text="❌ Шаблон не найден!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
            )
            return
        
        # Создаем временный шаблон с другим чатом
        temp_template = template.copy()
        temp_template['chat_id'] = target_chat_id
        
        # Создаем опрос
        # Вычисляем дату тренировки на основе дня тренировки в шаблоне
        training_day = temp_template['training_day']
        training_time = temp_template['training_time']
        
        # Получаем следующую дату для указанного дня недели
        from datetime import datetime, timedelta
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_day = days_map.get(training_day.lower())
        if target_day is None:
            await query.edit_message_text(
                text=f"❌ Неверный день недели: {training_day}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]])
            )
            return
        
        # Вычисляем дату следующего occurrence
        now = datetime.now()
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_training_date = now + timedelta(days=days_ahead)
        formatted_date = next_training_date.strftime('%d.%m.%Y')
        
        # Подставляем дату и время в описание
        description = temp_template['description'].replace('{date}', formatted_date).replace('{time}', training_time)
        
        poll_message = await volley_bot.create_poll(
            context.bot,
            temp_template['chat_id'],
            description,
            temp_template['options'],
            is_anonymous=False
        )
        
        if poll_message:
            # Закрепляем опрос
            await volley_bot.pin_message(context.bot, temp_template['chat_id'], poll_message.message_id)

            await query.edit_message_text(text=f"✅ Опрос '{temp_template['name']}' успешно создан и закреплен в чате {target_chat_id}!")
        else:
            await query.edit_message_text(text=f"❌ Ошибка при создании опроса '{temp_template['name']}' в чате {target_chat_id}.")
        
        # Возвращаемся к меню выбора шаблона
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    elif query.data == 'settings_menu':
        # Меню настроек
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить все опросы", callback_data='refresh_all_polls')],
            [InlineKeyboardButton("👥 Добавить администратора", callback_data='add_admin_menu')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="Меню настроек:",
            reply_markup=reply_markup
        )
        
    elif query.data == 'refresh_all_polls':
        # Обновление всех опросов
        await volley_bot.create_polls_for_all_enabled_templates(context.bot)
        await query.edit_message_text(
            text="✅ Все включенные опросы обновлены!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='settings_menu')]])
        )
        
    elif query.data == 'add_admin_menu':
        # Меню добавления администратора
        await query.edit_message_text(
            text="Для добавления нового администратора:\n\n"
                 "1. Добавьте будущего администратора в этот чат или начните с ним личный чат\n"
                 "2. Попросите его отправить команду /getid в этот чат\n"
                 "3. Скопируйте полученный ID и вернитесь сюда\n\n"
                 "Введите ID пользователя, которого хотите назначить администратором:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='settings_menu')]])
        )
        
        # Устанавливаем состояние ожидания ID админа для текущего пользователя
        user_id = update.effective_user.id
        creation_states[user_id] = {'step': 'waiting_admin_id'}
        
    elif query.data == 'back_to_main':
        # При возврате в главное меню сбрасываем состояние пользователя
        user_id = update.effective_user.id
        if user_id in creation_states:
            del creation_states[user_id]

        keyboard = [
            [
                InlineKeyboardButton("📊 Создать опрос", callback_data='create_poll_menu'),
            ],
            [
                InlineKeyboardButton("📋 Список опросов", callback_data='polls_list_menu'),
                InlineKeyboardButton("✏️ Редактировать шаблон", callback_data='edit_poll_menu')
            ],
            [
                InlineKeyboardButton("⚙️ Настройки", callback_data='settings_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text='🏐 Привет! Это бот для управления опросами о волейбольных тренировках.\n\n'
                 'Выберите действие:',
            reply_markup=reply_markup
        )


async def schedule_poll_creation(context: ContextTypes.DEFAULT_TYPE):
    """Функция для автоматического создания опросов по расписанию"""
    logger.info("Запуск автоматического создания опросов по расписанию")
    await volley_bot.create_polls_for_all_enabled_templates(context.bot)


def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(volley_bot.bot_token).build()

    # Создаем планировщик
    scheduler = AsyncIOScheduler()

    # Планируем создание опросов каждый день в 12:00 MSK
    # Бот проверит расписания и создаст опросы для тех, где сегодня день отправки
    scheduler.add_job(schedule_poll_creation,
                      CronTrigger(hour=12, minute=0),
                      args=(application.bot,))

    # Запускаем планировщик
    scheduler.start()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getid", get_user_id))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    logger.info("Запуск бота...")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()