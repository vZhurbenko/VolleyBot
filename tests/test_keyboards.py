#!/usr/bin/env python3
"""
Тесты для модуля keyboards.py
"""

import pytest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
    get_template_confirmation_keyboard
)


class TestGetMainMenu:
    """Тесты функции get_main_menu"""

    def test_returns_inline_keyboard_markup(self):
        result = get_main_menu()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_correct_buttons(self):
        result = get_main_menu()
        keyboard = result.inline_keyboard
        assert len(keyboard) == 3
        assert keyboard[0][0].text == "📊 Создать опрос"
        assert keyboard[0][0].callback_data == 'create_poll_menu'
        assert keyboard[1][0].text == "📋 Список опросов"
        assert keyboard[1][1].text == "✏️ Редактировать шаблон"
        assert keyboard[2][0].text == "⚙️ Настройки"


class TestGetBackKeyboard:
    """Тесты функции get_back_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_back_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_default_back_callback(self):
        result = get_back_keyboard()
        keyboard = result.inline_keyboard
        assert keyboard[0][0].callback_data == 'back_to_main'

    def test_custom_back_callback(self):
        result = get_back_keyboard('custom_callback')
        keyboard = result.inline_keyboard
        assert keyboard[0][0].callback_data == 'custom_callback'

    def test_button_text(self):
        result = get_back_keyboard()
        keyboard = result.inline_keyboard
        assert keyboard[0][0].text == "◀️ Назад"


class TestGetTrainingDaySelectionKeyboard:
    """Тесты функции get_training_day_selection_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_training_day_selection_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_all_days(self):
        result = get_training_day_selection_keyboard()
        keyboard = result.inline_keyboard
        days = [button.text for row in keyboard for button in row]
        expected_days = ["Понедельник", "Вторник", "Среда", "Четверг",
                         "Пятница", "Суббота", "Воскресенье"]
        assert days == expected_days

    def test_callback_data_format(self):
        result = get_training_day_selection_keyboard()
        keyboard = result.inline_keyboard
        for row in keyboard:
            assert row[0].callback_data.startswith("selected_day:")


class TestGetPollDaySelectionKeyboard:
    """Тесты функции get_poll_day_selection_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_poll_day_selection_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_all_days(self):
        result = get_poll_day_selection_keyboard()
        keyboard = result.inline_keyboard
        days = [button.text for row in keyboard for button in row]
        expected_days = ["Понедельник", "Вторник", "Среда", "Четверг",
                         "Пятница", "Суббота", "Воскресенье"]
        assert days == expected_days

    def test_callback_data_format(self):
        result = get_poll_day_selection_keyboard()
        keyboard = result.inline_keyboard
        for row in keyboard:
            assert row[0].callback_data.startswith("selected_poll_day:")


class TestGetCreationTypeKeyboard:
    """Тесты функции get_creation_type_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_creation_type_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_correct_buttons(self):
        result = get_creation_type_keyboard()
        keyboard = result.inline_keyboard
        assert len(keyboard) == 2
        assert keyboard[0][0].text == "📅 Создать расписание"
        assert keyboard[0][0].callback_data == "creation_type:schedule"
        assert keyboard[1][0].text == "📍 Один раз"
        assert keyboard[1][0].callback_data == "creation_type:once"


class TestGetCreateWithDefaultsKeyboard:
    """Тесты функции get_create_with_defaults_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_create_with_defaults_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_correct_buttons(self):
        result = get_create_with_defaults_keyboard()
        keyboard = result.inline_keyboard
        assert keyboard[0][0].text == "🚀 Создать опрос"
        assert keyboard[0][0].callback_data == 'create_with_defaults'
        assert keyboard[1][0].text == "◀️ Назад"
        assert keyboard[1][0].callback_data == 'create_poll_menu'


class TestGetSettingsMenuKeyboard:
    """Тесты функции get_settings_menu_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_settings_menu_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_correct_buttons(self):
        result = get_settings_menu_keyboard()
        keyboard = result.inline_keyboard
        assert keyboard[0][0].text == "🔄 Обновить все опросы"
        assert keyboard[1][0].text == "👥 Добавить администратора"
        assert keyboard[2][0].text == "◀️ Назад"


class TestGetEditTemplateKeyboard:
    """Тесты функции get_edit_template_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_edit_template_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_all_edit_options(self):
        result = get_edit_template_keyboard()
        keyboard = result.inline_keyboard
        button_texts = [button.text for row in keyboard for button in row]
        assert "✏️ Изменить название" in button_texts
        assert "✏️ Изменить описание" in button_texts
        assert "✏️ Изменить день тренировки" in button_texts
        assert "✏️ Изменить день опроса" in button_texts
        assert "✏️ Изменить время тренировки" in button_texts
        assert "✏️ Изменить варианты" in button_texts
        assert "◀️ Назад" in button_texts


class TestGetEditScheduleKeyboard:
    """Тесты функции get_edit_schedule_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_edit_schedule_keyboard("test-id")
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_all_edit_options(self):
        result = get_edit_schedule_keyboard("test-id")
        keyboard = result.inline_keyboard
        button_texts = [button.text for row in keyboard for button in row]
        assert "✏️ День тренировки" in button_texts
        assert "✏️ Время тренировки" in button_texts
        assert "✏️ День отправки" in button_texts
        assert "✏️ Время отправки" in button_texts
        assert "🔄 Вкл/Выкл" in button_texts
        assert "🗑️ Удалить расписание" in button_texts
        assert "◀️ Назад" in button_texts

    def test_callback_data_contains_schedule_id(self):
        result = get_edit_schedule_keyboard("my-schedule-id")
        keyboard = result.inline_keyboard
        for row in keyboard:
            for button in row:
                if button.callback_data and button.callback_data != 'polls_list_menu':
                    assert "my-schedule-id" in button.callback_data


class TestGetScheduleEditTrainingDayKeyboard:
    """Тесты функции get_schedule_edit_training_day_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_schedule_edit_training_day_keyboard("test-id")
        assert isinstance(result, InlineKeyboardMarkup)

    def test_callback_data_contains_schedule_id(self):
        result = get_schedule_edit_training_day_keyboard("my-schedule-id")
        keyboard = result.inline_keyboard
        for row in keyboard:
            assert "my-schedule-id" in row[0].callback_data


class TestGetScheduleEditPollDayKeyboard:
    """Тесты функции get_schedule_edit_poll_day_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_schedule_edit_poll_day_keyboard("test-id")
        assert isinstance(result, InlineKeyboardMarkup)

    def test_callback_data_contains_schedule_id(self):
        result = get_schedule_edit_poll_day_keyboard("my-schedule-id")
        keyboard = result.inline_keyboard
        for row in keyboard:
            assert "my-schedule-id" in row[0].callback_data


class TestGetPollsListKeyboard:
    """Тесты функции get_polls_list_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_polls_list_keyboard([])
        assert isinstance(result, InlineKeyboardMarkup)

    def test_empty_schedules(self):
        result = get_polls_list_keyboard([])
        keyboard = result.inline_keyboard
        assert len(keyboard) == 1
        assert keyboard[0][0].text == "◀️ Назад"

    def test_with_schedules(self):
        schedules = [
            {"id": "1", "name": "Schedule 1", "enabled": True},
            {"id": "2", "name": "Schedule 2", "enabled": False}
        ]
        result = get_polls_list_keyboard(schedules)
        keyboard = result.inline_keyboard
        assert len(keyboard) == 3  # 2 расписания + кнопка "Назад"
        assert "Schedule 1" in keyboard[0][0].text
        assert "✅ Вкл" in keyboard[0][0].text
        assert "Schedule 2" in keyboard[1][0].text
        assert "❌ Выкл" in keyboard[1][0].text

    def test_status_displayed_correctly(self):
        schedules = [
            {"id": "1", "name": "Enabled", "enabled": True},
            {"id": "2", "name": "Disabled", "enabled": False}
        ]
        result = get_polls_list_keyboard(schedules)
        keyboard = result.inline_keyboard
        assert "✅ Вкл" in keyboard[0][0].text
        assert "❌ Выкл" in keyboard[1][0].text


class TestGetTemplateConfirmationKeyboard:
    """Тесты функции get_template_confirmation_keyboard"""

    def test_returns_inline_keyboard_markup(self):
        result = get_template_confirmation_keyboard()
        assert isinstance(result, InlineKeyboardMarkup)

    def test_has_correct_buttons(self):
        result = get_template_confirmation_keyboard()
        keyboard = result.inline_keyboard
        assert keyboard[0][0].text == "✅ Создать"
        assert keyboard[0][0].callback_data == "confirm_create_template"
        assert keyboard[1][0].text == "❌ Отменить"
        assert keyboard[1][0].callback_data == "cancel_create_template"
