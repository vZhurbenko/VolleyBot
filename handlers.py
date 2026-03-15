#!/usr/bin/env python3
"""
Обработчики команд и callback для VolleyBot
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import Database
from utils import get_weekday_russian, get_day_of_week_number
from keyboards import (
    get_main_menu,
    get_back_keyboard,
    get_training_day_selection_keyboard,
    get_poll_day_selection_keyboard,
    get_creation_type_keyboard,
    get_create_with_defaults_keyboard,
    get_settings_menu_keyboard,
    get_edit_template_keyboard,
    get_edit_schedule_keyboard,
    get_schedule_edit_training_day_keyboard,
    get_schedule_edit_poll_day_keyboard,
    get_polls_list_keyboard,
    get_template_confirmation_keyboard,
    get_stats_menu_keyboard,
    get_stats_period_keyboard,
    get_stats_date_input_keyboard,
    get_user_stats_keyboard
)

logger = logging.getLogger(__name__)

# Глобальное состояние для создания опросов/расписаний
creation_states: Dict[int, Dict[str, Any]] = {}


async def create_once_poll(update, context, state):
    """Создание одноразового опроса"""
    try:
        target_day = get_day_of_week_number(state['training_day'])
        if target_day == -1:
            await update.message.reply_text(
                text=f"❌ Неверный день недели: {state['training_day']}"
            )
            return False

        now = datetime.now()
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        next_training_date = now + timedelta(days=days_ahead)
        formatted_date = next_training_date.strftime('%d.%m.%Y')
        weekday = get_weekday_russian(next_training_date)
        formatted_date_with_weekday = f"{formatted_date} ({weekday})"

        # Получаем описание из шаблона и подставляем дату и время
        template = context.bot_data['volley_bot'].get_default_template()
        description = template['description'].replace('{date}', formatted_date_with_weekday).replace('{time}', state['training_time'])

        poll_message = await context.bot_data['volley_bot'].create_poll(
            context.bot,
            state['chat_id'],
            description,
            template['options'],
            is_anonymous=False,
            message_thread_id=state.get('thread_id')
        )

        if poll_message:
            await context.bot_data['volley_bot'].pin_message(context.bot, state['chat_id'], poll_message.message_id)

            thread_info = f" (топик {state.get('thread_id')})" if state.get('thread_id') else ''
            await update.message.reply_text(
                text=f"✅ Опрос успешно создан и закреплен в чате {state['chat_id']}{thread_info}!\n\n"
                     f"Опрос создан единоразово, без автоматического повторения."
            )
            logger.info(f"Одноразовый опрос создан в чате {state['chat_id']}")
            return True
        else:
            await update.message.reply_text(
                text=f"❌ Ошибка при создании опроса в чате {state['chat_id']}."
            )
            return False
    except Exception as e:
        logger.error(f"Ошибка при создании одноразового опроса: {e}")
        await update.message.reply_text(
            text=f"❌ Ошибка при создании опроса: {e}"
        )
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    volley_bot = context.bot_data['volley_bot']
    
    user_id = update.effective_user.id
    if user_id not in volley_bot.admin_user_ids:
        await update.message.reply_text('❌ У вас нет прав для управления этим ботом.')
        return

    await update.message.reply_text(
        '🏐 Привет! Это бот для управления опросами о волейбольных тренировках.\n\n'
        'Выберите действие:',
        reply_markup=get_main_menu()
    )


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


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - показать статистику тренировок"""
    volley_bot = context.bot_data['volley_bot']

    user_id = update.effective_user.id
    if user_id not in volley_bot.admin_user_ids:
        await update.message.reply_text('❌ У вас нет прав для управления этим ботом.')
        return

    await update.message.reply_text(
        text="📊 **Статистика тренировок**\n\n"
             "Выберите раздел статистики:",
        reply_markup=get_stats_menu_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений для создания шаблонов"""
    volley_bot = context.bot_data['volley_bot']
    user_id = update.effective_user.id

    if user_id not in volley_bot.admin_user_ids:
        return

    if user_id not in creation_states:
        return

    state = creation_states[user_id]
    message_text = update.message.text.strip()

    if state['step'] == 'changing_name':
        template = volley_bot.get_default_template()
        template['name'] = message_text
        volley_bot.update_default_template(template)

        await update.message.reply_text(f"Название шаблона изменено на: {message_text}")
        del creation_states[user_id]

    elif state['step'] == 'changing_description':
        template = volley_bot.get_default_template()
        template['description'] = message_text
        volley_bot.update_default_template(template)

        await update.message.reply_text(f"Описание шаблона изменено на: {message_text}")
        del creation_states[user_id]

    elif state['step'] == 'changing_training_time':
        template = volley_bot.get_default_template()
        template['training_time'] = message_text
        volley_bot.update_default_template(template)

        await update.message.reply_text(f"Время тренировки изменено на: {message_text}")
        del creation_states[user_id]

    elif state['step'] == 'changing_options':
        options = [opt.strip() for opt in message_text.split('\n') if opt.strip()]
        if len(options) < 2:
            await update.message.reply_text("Пожалуйста, введите хотя бы 2 варианта ответа, каждый на новой строке.")
            return

        template = volley_bot.get_default_template()
        template['options'] = options
        volley_bot.update_default_template(template)

        await update.message.reply_text(f"Варианты ответа изменены. Теперь их {len(options)}.")
        del creation_states[user_id]

    elif state['step'] == 'waiting_admin_id':
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

        del creation_states[user_id]

    elif state['step'] == 'waiting_training_time_input':
        training_time = message_text
        creation_type = state.get('creation_type', 'schedule')

        if creation_type == 'once':
            creation_states[user_id] = {
                'step': 'ready_to_create_once',
                'chat_id': state['chat_id'],
                'thread_id': state['thread_id'],
                'training_day': state['training_day'],
                'training_time': training_time
            }

            await create_once_poll(update, context, creation_states[user_id])
            del creation_states[user_id]
        else:
            schedule_id = str(uuid.uuid4())
            schedule = {
                'id': schedule_id,
                'name': f"Расписание {state['training_day']}->{state['poll_day']}",
                'chat_id': state['chat_id'],
                'message_thread_id': state['thread_id'],
                'training_day': state['training_day'],
                'poll_day': state['poll_day'],
                'training_time': training_time,
                'poll_time': '12:00',
                'enabled': True
            }

            volley_bot.add_poll_schedule(schedule)

            thread_info = f" (топик {state['thread_id']})" if state['thread_id'] else ""
            await update.message.reply_text(
                text=f"✅ Расписание успешно создано!\n\n"
                     f"📋 Параметры:\n"
                     f"День тренировки: {state['training_day']}\n"
                     f"Время тренировки: {training_time}\n"
                     f"День отправки опроса: {state['poll_day']}\n"
                     f"Время отправки опроса: 12:00 (MSK)\n"
                     f"Чат: {state['chat_id']}" + thread_info + "\n\n"
                     f"Опросы будут автоматически создаваться каждый {state['poll_day']} в 12:00 для тренировки в {state['training_day']}.",
                reply_markup=get_back_keyboard('polls_list_menu')
            )

            del creation_states[user_id]

    elif state['step'] == 'schedule_changing_time':
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
            reply_markup=get_back_keyboard(f"edit_schedule:{schedule_id}")
        )

        del creation_states[user_id]

    elif state['step'] == 'schedule_changing_poll_time':
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
            reply_markup=get_back_keyboard(f"edit_schedule:{schedule_id}")
        )

        del creation_states[user_id]

    elif state['step'] == 'waiting_options':
        options = [opt.strip() for opt in message_text.split('\n') if opt.strip()]
        if len(options) < 2:
            await update.message.reply_text("Пожалуйста, введите хотя бы 2 варианта ответа, каждый на новой строке.")
            return

        state['options'] = options
        state['step'] = 'confirm_creation'

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

        await update.message.reply_text(summary, reply_markup=get_template_confirmation_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()

    volley_bot = context.bot_data['volley_bot']
    user_id = update.effective_user.id
    
    if user_id not in volley_bot.admin_user_ids:
        await query.answer(text='❌ У вас нет прав для управления этим ботом.', show_alert=True)
        return

    if query.data == 'create_poll_menu':
        template = volley_bot.get_default_template()
        default_chat_id = template.get('default_chat_id', '')

        if not default_chat_id:
            await query.edit_message_text(
                text="❌ Не задан чат по умолчанию в шаблоне.\n\n"
                     "Настройте шаблон опроса в разделе '✏️ Редактировать шаблон'",
                reply_markup=get_back_keyboard()
            )
            return

        info_text = f"📍 Чат: {default_chat_id}\n"
        default_topic_id = template.get('default_topic_id', None)
        if default_topic_id:
            info_text += f"📍 Топик: {default_topic_id}\n"

        await query.edit_message_text(
            text=f"Значения по умолчанию:\n{info_text}\n\nНажмите кнопку ниже для создания опроса:",
            reply_markup=get_create_with_defaults_keyboard()
        )

    elif query.data == 'create_with_defaults':
        template = volley_bot.get_default_template()
        default_chat_id = template.get('default_chat_id', '')

        if not default_chat_id:
            await query.edit_message_text(
                text="❌ Не задан чат по умолчанию в шаблоне.",
                reply_markup=get_back_keyboard('create_poll_menu')
            )
            return

        default_topic_id = template.get('default_topic_id', None)
        creation_states[user_id] = {
            'step': 'waiting_training_day',
            'chat_id': default_chat_id,
            'thread_id': default_topic_id
        }

        await query.edit_message_text(
            text="Выберите день недели, в который будет тренировка:",
            reply_markup=get_training_day_selection_keyboard()
        )

    elif query.data.startswith('create_poll:'):
        parts = query.data.split(':')
        if len(parts) >= 2:
            target_chat_id = parts[1]
        else:
            await query.edit_message_text(
                text="❌ Неверный формат данных.",
                reply_markup=get_back_keyboard('create_poll_menu')
            )
            return

        poll_message = await volley_bot.create_poll_from_template(context.bot, target_chat_id)

        if poll_message:
            await query.edit_message_text(text=f"✅ Опрос успешно создан и закреплен в чате {target_chat_id}!")
        else:
            await query.edit_message_text(text=f"❌ Ошибка при создании опроса в чате {target_chat_id}.")

        await query.edit_message_reply_markup(reply_markup=get_back_keyboard('create_poll_menu'))

    elif query.data == 'polls_list_menu':
        schedules = volley_bot.get_poll_schedules()

        if not schedules:
            await query.edit_message_text(
                text="❌ Нет активных расписаний опросов.\n\n"
                     "Нажмите '📊 Создать опрос', чтобы добавить новое расписание.",
                reply_markup=get_back_keyboard()
            )
            return

        await query.edit_message_text(
            text="📋 Список расписаний опросов:\n\n"
                 "Выберите опрос для редактирования настроек:",
            reply_markup=get_polls_list_keyboard(schedules)
        )

    elif query.data.startswith('edit_schedule:'):
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
                reply_markup=get_back_keyboard('polls_list_menu')
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

        await query.edit_message_text(text=info, reply_markup=get_edit_schedule_keyboard(schedule_id))

    elif query.data.startswith('schedule_edit_training_day:'):
        schedule_id = query.data.split(':')[1]
        await query.edit_message_text(
            text="Выберите новый день тренировки:",
            reply_markup=get_schedule_edit_training_day_keyboard(schedule_id)
        )

    elif query.data.startswith('schedule_set_training_day:'):
        parts = query.data.split(':')
        schedule_id = parts[1]
        new_day = parts[2]

        schedules = volley_bot.get_poll_schedules()
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule['training_day'] = new_day
                schedule['name'] = f"Расписание {new_day}->{schedule['poll_day']}"
                volley_bot.save_config()
                break

        await query.edit_message_text(
            text=f"✅ День тренировки изменен на {new_day}",
            reply_markup=get_back_keyboard(f"edit_schedule:{schedule_id}")
        )

    elif query.data.startswith('schedule_edit_training_time:'):
        schedule_id = query.data.split(':')[1]
        creation_states[user_id] = {
            'step': 'schedule_changing_time',
            'schedule_id': schedule_id
        }

        await query.edit_message_text(
            text="Введите новое время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
            reply_markup=get_back_keyboard(f"edit_schedule:{schedule_id}")
        )

    elif query.data.startswith('schedule_edit_poll_day:'):
        schedule_id = query.data.split(':')[1]
        await query.edit_message_text(
            text="Выберите новый день отправки опроса:",
            reply_markup=get_schedule_edit_poll_day_keyboard(schedule_id)
        )

    elif query.data.startswith('schedule_set_poll_day:'):
        parts = query.data.split(':')
        schedule_id = parts[1]
        new_day = parts[2]

        schedules = volley_bot.get_poll_schedules()
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule['poll_day'] = new_day
                schedule['name'] = f"Расписание {schedule['training_day']}->{new_day}"
                volley_bot.save_config()
                break

        await query.edit_message_text(
            text=f"✅ День отправки опроса изменен на {new_day}",
            reply_markup=get_back_keyboard(f"edit_schedule:{schedule_id}")
        )

    elif query.data.startswith('schedule_edit_poll_time:'):
        schedule_id = query.data.split(':')[1]
        creation_states[user_id] = {
            'step': 'schedule_changing_poll_time',
            'schedule_id': schedule_id
        }

        await query.edit_message_text(
            text="Введите новое время отправки опроса в формате ЧЧ:ММ (например, 12:00):",
            reply_markup=get_back_keyboard(f"edit_schedule:{schedule_id}")
        )

    elif query.data.startswith('schedule_toggle_enabled:'):
        schedule_id = query.data.split(':')[1]

        schedules = volley_bot.get_poll_schedules()
        for schedule in schedules:
            if schedule['id'] == schedule_id:
                schedule['enabled'] = not schedule.get('enabled', True)
                volley_bot.save_config()
                status = "включено" if schedule['enabled'] else "выключено"
                await query.edit_message_text(
                    text=f"✅ Расписание {status}",
                    reply_markup=get_back_keyboard(f"edit_schedule:{schedule_id}")
                )
                break

    elif query.data.startswith('schedule_delete:'):
        schedule_id = query.data.split(':')[1]
        volley_bot.remove_poll_schedule(schedule_id)

        await query.edit_message_text(
            text="✅ Расписание успешно удалено!",
            reply_markup=get_back_keyboard('polls_list_menu')
        )

    elif query.data == 'edit_poll_menu':
        template = volley_bot.get_default_template()

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

        keyboard = [[InlineKeyboardButton("✏️ Редактировать шаблон", callback_data="edit_default_template")]]
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')])
        
        await query.edit_message_text(
            text=info,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == 'edit_default_template':
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

        await query.edit_message_text(text=info, reply_markup=get_edit_template_keyboard())

    elif query.data == 'change_name':
        creation_states[user_id] = {'step': 'changing_name'}
        await query.edit_message_text(
            text="Введите новое название шаблона:",
            reply_markup=get_back_keyboard('edit_default_template')
        )

    elif query.data == 'change_description':
        creation_states[user_id] = {'step': 'changing_description'}
        await query.edit_message_text(
            text="Введите новое описание шаблона (используйте {date} и {time}):",
            reply_markup=get_back_keyboard('edit_default_template')
        )

    elif query.data == 'change_training_day':
        creation_states[user_id] = {'step': 'changing_training_day'}
        await query.edit_message_text(
            text="Выберите день недели, в который будет тренировка:",
            reply_markup=get_training_day_selection_keyboard()
        )

    elif query.data == 'change_poll_day':
        creation_states[user_id] = {'step': 'changing_poll_day'}
        await query.edit_message_text(
            text="Выберите день недели, в который бот должен создавать опрос:",
            reply_markup=get_poll_day_selection_keyboard()
        )

    elif query.data == 'change_training_time':
        creation_states[user_id] = {'step': 'changing_training_time'}
        await query.edit_message_text(
            text="Введите время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
            reply_markup=get_back_keyboard('edit_default_template')
        )

    elif query.data == 'change_options':
        creation_states[user_id] = {'step': 'changing_options'}
        await query.edit_message_text(
            text="Введите варианты ответов, каждый на новой строке:\n\n"
                 "Пример:\n"
                 "Буду\n"
                 "Не буду\n"
                 "Возможно",
            reply_markup=get_back_keyboard('edit_default_template')
        )

    elif query.data.startswith('selected_day:'):
        selected_day = query.data.split(':')[1]

        if user_id in creation_states:
            state = creation_states[user_id]
            if state['step'] == 'waiting_training_day':
                creation_states[user_id] = {
                    'step': 'waiting_creation_type',
                    'chat_id': state['chat_id'],
                    'thread_id': state['thread_id'],
                    'training_day': selected_day
                }

                await query.edit_message_text(
                    text=f"День тренировки: {selected_day}\n\n"
                         "Как создать опрос?",
                    reply_markup=get_creation_type_keyboard()
                )
            else:
                await query.answer(text="Ошибка: неверное состояние", show_alert=True)
        else:
            template = volley_bot.get_default_template()
            template['training_day'] = selected_day
            volley_bot.update_default_template(template)

            await query.edit_message_text(
                text=f"День тренировки изменен на {selected_day}",
                reply_markup=get_back_keyboard('edit_default_template')
            )

    elif query.data.startswith('creation_type:'):
        creation_type = query.data.split(':')[1]

        if user_id not in creation_states:
            await query.answer(text="Ошибка: состояние не найдено", show_alert=True)
            return

        state = creation_states[user_id]
        if state['step'] != 'waiting_creation_type':
            await query.answer(text="Ошибка: неверное состояние", show_alert=True)
            return

        if creation_type == 'schedule':
            creation_states[user_id]['step'] = 'waiting_poll_day'

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

        elif creation_type == 'once':
            creation_states[user_id]['step'] = 'waiting_training_time_input'
            creation_states[user_id]['creation_type'] = 'once'

            await query.edit_message_text(
                text="Введите время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
                reply_markup=get_back_keyboard('create_poll_menu')
            )

    elif query.data.startswith('selected_poll_day:'):
        selected_day = query.data.split(':')[1]

        template = volley_bot.get_default_template()
        template['poll_day'] = selected_day
        volley_bot.update_default_template(template)

        await query.edit_message_text(
            text=f"День опроса изменен на {selected_day}",
            reply_markup=get_back_keyboard('edit_default_template')
        )

    elif query.data.startswith('poll_day_selection:'):
        selected_day = query.data.split(':')[1]

        if user_id in creation_states:
            state = creation_states[user_id]
            if state['step'] == 'waiting_poll_day':
                creation_states[user_id] = {
                    'step': 'waiting_training_time_input',
                    'chat_id': state['chat_id'],
                    'thread_id': state['thread_id'],
                    'training_day': state['training_day'],
                    'poll_day': selected_day,
                    'creation_type': 'schedule'
                }

                await query.edit_message_text(
                    text="Введите время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
                    reply_markup=get_back_keyboard('create_poll_menu')
                )
            else:
                await query.answer(text="Ошибка: неверное состояние", show_alert=True)
        else:
            template = volley_bot.get_default_template()
            template['poll_day'] = selected_day
            volley_bot.update_default_template(template)

            await query.edit_message_text(
                text=f"День опроса изменен на {selected_day}",
                reply_markup=get_back_keyboard('edit_default_template')
            )

    elif query.data == 'create_schedule_yes':
        await query.answer(text="Выберите день тренировки и введите время", show_alert=True)

    elif query.data == 'create_schedule_no':
        await query.answer(text="Выберите день тренировки и введите время", show_alert=True)

    elif query.data.startswith('poll_day:'):
        selected_day = query.data.split(':')[1]

        if user_id in creation_states:
            state = creation_states[user_id]
            if state['step'] == 'waiting_poll_day':
                creation_states[user_id]['poll_day'] = selected_day
                creation_states[user_id]['step'] = 'waiting_training_time_input'

                await query.edit_message_text(
                    text="Введите время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00):",
                    reply_markup=get_back_keyboard('create_poll_menu')
                )
            else:
                await query.answer(text="Ошибка: неверное состояние", show_alert=True)
        else:
            template = volley_bot.get_default_template()
            template['poll_day'] = selected_day
            volley_bot.update_default_template(template)

            await query.edit_message_text(
                text=f"День опроса изменен на {selected_day}",
                reply_markup=get_back_keyboard('edit_default_template')
            )

    elif query.data == 'confirm_create_template':
        if user_id in creation_states:
            state = creation_states[user_id]

            template_id = str(uuid.uuid4())

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

            volley_bot.add_poll_template(new_template)

            del creation_states[user_id]

            await query.edit_message_text(
                text=f"✅ Шаблон '{state['name']}' успешно создан!",
                reply_markup=get_back_keyboard('edit_poll_menu')
            )
        else:
            await query.answer(text="Ошибка: состояние не найдено", show_alert=True)

    elif query.data == 'cancel_create_template':
        if user_id in creation_states:
            del creation_states[user_id]

        await query.edit_message_text(
            text="❌ Создание шаблона отменено.",
            reply_markup=get_back_keyboard('edit_poll_menu')
        )

    elif query.data == 'create_template_start':
        creation_states[user_id] = {'step': 'waiting_name'}

        await query.edit_message_text(
            text="Введите название для нового шаблона опроса:",
            reply_markup=get_back_keyboard('edit_poll_menu')
        )

    elif query.data.startswith('create_poll:'):
        parts = query.data.split(':')
        template_id = parts[1]
        target_chat_id = parts[2]

        template = volley_bot.get_poll_template_by_id(template_id)
        if not template:
            await query.edit_message_text(
                text="❌ Шаблон не найден!",
                reply_markup=get_back_keyboard('create_poll_menu')
            )
            return

        temp_template = template.copy()
        temp_template['chat_id'] = target_chat_id

        training_day = temp_template['training_day']
        training_time = temp_template['training_time']

        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }

        target_day = days_map.get(training_day.lower())
        if target_day is None:
            await query.edit_message_text(
                text=f"❌ Неверный день недели: {training_day}",
                reply_markup=get_back_keyboard('create_poll_menu')
            )
            return

        now = datetime.now()
        days_ahead = target_day - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7

        next_training_date = now + timedelta(days=days_ahead)
        formatted_date = next_training_date.strftime('%d.%m.%Y')
        weekday = get_weekday_russian(next_training_date)
        formatted_date_with_weekday = f"{formatted_date} ({weekday})"

        description = temp_template['description'].replace('{date}', formatted_date_with_weekday).replace('{time}', training_time)

        poll_message = await volley_bot.create_poll(
            context.bot,
            temp_template['chat_id'],
            description,
            temp_template['options'],
            is_anonymous=False
        )

        if poll_message:
            await volley_bot.pin_message(context.bot, temp_template['chat_id'], poll_message.message_id)
            await query.edit_message_text(text=f"✅ Опрос '{temp_template['name']}' успешно создан и закреплен в чате {target_chat_id}!")
        else:
            await query.edit_message_text(text=f"❌ Ошибка при создании опроса '{temp_template['name']}' в чате {target_chat_id}.")

        await query.edit_message_reply_markup(reply_markup=get_back_keyboard('create_poll_menu'))

    elif query.data == 'settings_menu':
        await query.edit_message_text(
            text="Меню настроек:",
            reply_markup=get_settings_menu_keyboard()
        )

    elif query.data == 'refresh_all_polls':
        await volley_bot.create_polls_for_all_enabled_templates(context.bot)
        await query.edit_message_text(
            text="✅ Все включенные опросы обновлены!",
            reply_markup=get_back_keyboard('settings_menu')
        )

    elif query.data == 'add_admin_menu':
        await query.edit_message_text(
            text="Для добавления нового администратора:\n\n"
                 "1. Добавьте будущего администратора в этот чат или начните с ним личный чат\n"
                 "2. Попросите его отправить команду /getid в этот чат\n"
                 "3. Скопируйте полученный ID и вернитесь сюда\n\n"
                 "Введите ID пользователя, которого хотите назначить администратором:",
            reply_markup=get_back_keyboard('settings_menu')
        )

        creation_states[user_id] = {'step': 'waiting_admin_id'}

    elif query.data == 'back_to_main':
        if user_id in creation_states:
            del creation_states[user_id]

        await query.edit_message_text(
            text='🏐 Привет! Это бот для управления опросами о волейбольных тренировках.\n\n'
                 'Выберите действие:',
            reply_markup=get_main_menu()
        )

    # ==================== Обработчики статистики ====================

    elif query.data == 'stats_menu':
        await query.edit_message_text(
            text="📊 **Статистика тренировок**\n\n"
                 "Выберите раздел статистики:",
            reply_markup=get_stats_menu_keyboard()
        )

    elif query.data == 'stats_overview':
        await query.edit_message_text(
            text="📈 **Общая статистика**\n\nВыберите период:",
            reply_markup=get_stats_period_keyboard('overview')
        )

    elif query.data == 'stats_top_users':
        await query.edit_message_text(
            text="👥 **Топ пользователей**\n\nВыберите период:",
            reply_markup=get_stats_period_keyboard('top_users')
        )

    elif query.data == 'stats_by_date':
        await query.edit_message_text(
            text="📅 **Статистика по дате**\n\n"
                 "Выберите дату для просмотра детальной статистики:",
            reply_markup=get_stats_date_input_keyboard()
        )

    elif query.data.startswith('stats_period:'):
        parts = query.data.split(':')
        period = parts[1]
        stats_type = parts[2] if len(parts) > 2 else 'overview'

        stats = volley_bot.db.get_training_stats(period)

        if 'error' in stats:
            await query.edit_message_text(text=f"❌ Ошибка: {stats['error']}")
            return

        period_names = {
            'day': 'день',
            'week': 'неделю',
            'month': 'месяц',
            'all': 'всё время'
        }

        text = (
            f"📈 **Общая статистика за {period_names.get(period, period)}**\n\n"
            f"📅 Период: {stats['date_range']['from']} - {stats['date_range']['to']}\n\n"
            f"🏐 Тренировок: {stats.get('total_trainings', 0)}\n"
            f"👥 Всего записей: {stats.get('total_signups', 0)}\n"
            f"👤 Уникальных пользователей: {stats.get('unique_users', 0)}\n"
            f"👥 Авторизованных: {stats.get('users_count', 0)}\n"
            f"👻 Гостей: {stats.get('guests_count', 0)}\n"
            f"📊 В среднем на тренировку: {stats.get('avg_per_training', 0)}"
        )

        await query.edit_message_text(
            text=text,
            reply_markup=get_stats_period_keyboard(stats_type)
        )

    elif query.data.startswith('stats_date:'):
        date_type = query.data.split(':')[1]
        from datetime import timedelta

        now = datetime.now()
        if date_type == 'today':
            target_date = now.strftime('%Y-%m-%d')
            display_date = now.strftime('%d.%m.%Y')
        elif date_type == 'yesterday':
            yesterday = now - timedelta(days=1)
            target_date = yesterday.strftime('%Y-%m-%d')
            display_date = yesterday.strftime('%d.%m.%Y')
        else:
            await query.edit_message_text(
                text="❌ Неверный формат даты",
                reply_markup=get_stats_date_input_keyboard()
            )
            return

        details = volley_bot.db.get_training_details(target_date)

        if 'error' in details:
            await query.edit_message_text(
                text=f"❌ Ошибка: {details['error']}",
                reply_markup=get_stats_date_input_keyboard()
            )
            return

        training_info = details.get('training_info', {})
        stats = details.get('stats', {})
        participants = details.get('participants', [])

        text = (
            f"📅 **Статистика за {display_date}**\n\n"
        )

        if training_info:
            text += (
                f"🏐 **{training_info.get('name', 'Тренировка')}**\n"
                f"⏰ Время: {training_info.get('start_time', 'Н/Д')} - {training_info.get('end_time', 'Н/Д')}\n"
                f"📍 Место: {training_info.get('location', 'Н/Д')}\n\n"
            )

        text += (
            f"📊 **Итого:**\n"
            f"Всего участников: {stats.get('total', 0)}\n"
            f"👥 Авторизованных: {stats.get('users_count', 0)}\n"
            f"👻 Гостей: {stats.get('guests_count', 0)}\n"
        )

        if participants:
            text += "\n**Участники:**\n"
            for i, p in enumerate(participants[:20], 1):  # Показываем до 20 участников
                guest_mark = "👻 " if p.get('is_guest', False) else ""
                username = p.get('username', '')
                name = f"@{username}" if username else f"{p.get('first_name', '')} {p.get('last_name', '')}"
                text += f"{i}. {guest_mark}{name.strip()}\n"

            if len(participants) > 20:
                text += f"\n... и ещё {len(participants) - 20} участников"

        await query.edit_message_text(
            text=text,
            reply_markup=get_stats_date_input_keyboard()
        )

    elif query.data.startswith('user_stats_period:'):
        parts = query.data.split(':')
        period = parts[1]
        user_telegram_id = int(parts[2])

        user_stats = volley_bot.db.get_user_stats(user_telegram_id, period)

        if 'error' in user_stats:
            await query.answer(text=f"❌ Ошибка: {user_stats['error']}", show_alert=True)
            return

        user_info = user_stats.get('user_info', {})
        stats = user_stats.get('stats', {})

        period_names = {
            'week': 'неделю',
            'month': 'месяц',
            'all': 'всё время'
        }

        guest_mark = "👻 " if user_info.get('is_guest', False) else ""
        username = user_info.get('username', '')
        name = f"@{username}" if username else f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}"

        text = (
            f"👤 **Статистика: {guest_mark}{name}**\n\n"
            f"📅 Период: {user_stats['date_range']['from']} - {user_stats['date_range']['to']}\n\n"
            f"🏐 Тренировок записался: {stats.get('total_trainings', 0)}\n"
            f"✅ Посещено: {stats.get('attended_trainings', 0)}\n"
            f"⏳ В листе ожидания: {stats.get('waitlist_count', 0)}\n"
            f"👻 Записей как гость: {stats.get('guests_trainings', 0)}\n"
        )

        if stats.get('last_activity'):
            last_activity = stats['last_activity']
            if isinstance(last_activity, str):
                text += f"🕒 Последняя активность: {last_activity[:16]}"

        await query.edit_message_text(
            text=text,
            reply_markup=get_user_stats_keyboard(user_telegram_id)
        )

    elif query.data.startswith('stats_date_select:'):
        # Обработка выбора конкретной даты (для будущего расширения)
        await query.answer(text="Функция в разработке", show_alert=True)

