#!/usr/bin/env python3
"""
Фабрики клавиатур для VolleyBot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [InlineKeyboardButton("📊 Создать опрос", callback_data='create_poll_menu')],
        [
            InlineKeyboardButton("📋 Список опросов", callback_data='polls_list_menu'),
            InlineKeyboardButton("✏️ Редактировать шаблон", callback_data='edit_poll_menu')
        ],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(back_callback: str = 'back_to_main') -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой 'Назад'"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=back_callback)]])


def get_training_day_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора дня тренировки"""
    keyboard = [
        [InlineKeyboardButton("Понедельник", callback_data="selected_day:monday")],
        [InlineKeyboardButton("Вторник", callback_data="selected_day:tuesday")],
        [InlineKeyboardButton("Среда", callback_data="selected_day:wednesday")],
        [InlineKeyboardButton("Четверг", callback_data="selected_day:thursday")],
        [InlineKeyboardButton("Пятница", callback_data="selected_day:friday")],
        [InlineKeyboardButton("Суббота", callback_data="selected_day:saturday")],
        [InlineKeyboardButton("Воскресенье", callback_data="selected_day:sunday")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_poll_day_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора дня создания опроса"""
    keyboard = [
        [InlineKeyboardButton("Понедельник", callback_data="selected_poll_day:monday")],
        [InlineKeyboardButton("Вторник", callback_data="selected_poll_day:tuesday")],
        [InlineKeyboardButton("Среда", callback_data="selected_poll_day:wednesday")],
        [InlineKeyboardButton("Четверг", callback_data="selected_poll_day:thursday")],
        [InlineKeyboardButton("Пятница", callback_data="selected_poll_day:friday")],
        [InlineKeyboardButton("Суббота", callback_data="selected_poll_day:saturday")],
        [InlineKeyboardButton("Воскресенье", callback_data="selected_poll_day:sunday")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_creation_type_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора типа создания (расписание/один раз)"""
    keyboard = [
        [InlineKeyboardButton("📅 Создать расписание", callback_data="creation_type:schedule")],
        [InlineKeyboardButton("📍 Один раз", callback_data="creation_type:once")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_create_with_defaults_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура создания опроса с значениями по умолчанию"""
    keyboard = [
        [InlineKeyboardButton("🚀 Создать опрос", callback_data='create_with_defaults')],
        [InlineKeyboardButton("◀️ Назад", callback_data='create_poll_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек"""
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить все опросы", callback_data='refresh_all_polls')],
        [InlineKeyboardButton("👥 Добавить администратора", callback_data='add_admin_menu')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_template_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура редактирования шаблона"""
    keyboard = [
        [InlineKeyboardButton("✏️ Изменить название", callback_data='change_name')],
        [InlineKeyboardButton("✏️ Изменить описание", callback_data='change_description')],
        [InlineKeyboardButton("✏️ Изменить день тренировки", callback_data='change_training_day')],
        [InlineKeyboardButton("✏️ Изменить день опроса", callback_data='change_poll_day')],
        [InlineKeyboardButton("✏️ Изменить время тренировки", callback_data='change_training_time')],
        [InlineKeyboardButton("✏️ Изменить варианты", callback_data='change_options')],
        [InlineKeyboardButton("◀️ Назад", callback_data='edit_poll_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_edit_schedule_keyboard(schedule_id: str) -> InlineKeyboardMarkup:
    """Клавиатура редактирования расписания"""
    keyboard = [
        [InlineKeyboardButton("✏️ День тренировки", callback_data=f"schedule_edit_training_day:{schedule_id}")],
        [InlineKeyboardButton("✏️ Время тренировки", callback_data=f"schedule_edit_training_time:{schedule_id}")],
        [InlineKeyboardButton("✏️ День отправки", callback_data=f"schedule_edit_poll_day:{schedule_id}")],
        [InlineKeyboardButton("✏️ Время отправки", callback_data=f"schedule_edit_poll_time:{schedule_id}")],
        [InlineKeyboardButton("🔄 Вкл/Выкл", callback_data=f"schedule_toggle_enabled:{schedule_id}")],
        [InlineKeyboardButton("🗑️ Удалить расписание", callback_data=f"schedule_delete:{schedule_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data='polls_list_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_schedule_edit_training_day_keyboard(schedule_id: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора дня тренировки для расписания"""
    keyboard = [
        [InlineKeyboardButton("Понедельник", callback_data=f"schedule_set_training_day:{schedule_id}:monday")],
        [InlineKeyboardButton("Вторник", callback_data=f"schedule_set_training_day:{schedule_id}:tuesday")],
        [InlineKeyboardButton("Среда", callback_data=f"schedule_set_training_day:{schedule_id}:wednesday")],
        [InlineKeyboardButton("Четверг", callback_data=f"schedule_set_training_day:{schedule_id}:thursday")],
        [InlineKeyboardButton("Пятница", callback_data=f"schedule_set_training_day:{schedule_id}:friday")],
        [InlineKeyboardButton("Суббота", callback_data=f"schedule_set_training_day:{schedule_id}:saturday")],
        [InlineKeyboardButton("Воскресенье", callback_data=f"schedule_set_training_day:{schedule_id}:sunday")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_schedule_edit_poll_day_keyboard(schedule_id: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора дня отправки опроса для расписания"""
    keyboard = [
        [InlineKeyboardButton("Понедельник", callback_data=f"schedule_set_poll_day:{schedule_id}:monday")],
        [InlineKeyboardButton("Вторник", callback_data=f"schedule_set_poll_day:{schedule_id}:tuesday")],
        [InlineKeyboardButton("Среда", callback_data=f"schedule_set_poll_day:{schedule_id}:wednesday")],
        [InlineKeyboardButton("Четверг", callback_data=f"schedule_set_poll_day:{schedule_id}:thursday")],
        [InlineKeyboardButton("Пятница", callback_data=f"schedule_set_poll_day:{schedule_id}:friday")],
        [InlineKeyboardButton("Суббота", callback_data=f"schedule_set_poll_day:{schedule_id}:saturday")],
        [InlineKeyboardButton("Воскресенье", callback_data=f"schedule_set_poll_day:{schedule_id}:sunday")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_polls_list_keyboard(schedules: list) -> InlineKeyboardMarkup:
    """Клавиатура списка расписаний"""
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
    return InlineKeyboardMarkup(keyboard)


def get_template_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения создания шаблона"""
    keyboard = [
        [InlineKeyboardButton("✅ Создать", callback_data="confirm_create_template")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_create_template")]
    ]
    return InlineKeyboardMarkup(keyboard)
