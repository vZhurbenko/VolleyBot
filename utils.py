#!/usr/bin/env python3
"""
Утилиты для VolleyBot
"""

from datetime import datetime, timedelta
from typing import Dict


def get_weekday_russian(date: datetime) -> str:
    """Получение дня недели на русском языке"""
    weekdays = {
        0: 'понедельник',
        1: 'вторник',
        2: 'среда',
        3: 'четверг',
        4: 'пятница',
        5: 'суббота',
        6: 'воскресенье'
    }
    return weekdays.get(date.weekday(), '')


def get_day_of_week_number(day_of_week: str) -> int:
    """Преобразование названия дня недели в число (0-6, где 0 - понедельник)"""
    days_map = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    return days_map.get(day_of_week.lower(), -1)


async def get_next_occurrence(day_of_week: str, time_str: str) -> datetime:
    """
    Вычисление следующего occurrence события
    
    Args:
        day_of_week: День недели на английском (monday, tuesday, ...)
        time_str: Время в формате HH:MM
    
    Returns:
        datetime следующего occurrence
    """
    target_day = get_day_of_week_number(day_of_week)
    if target_day == -1:
        raise ValueError(f"Неверный день недели: {day_of_week}")

    # Разбираем время
    hour, minute = map(int, time_str.split(':'))

    # Получаем текущую дату и время
    now = datetime.now()

    # Вычисляем дату следующего occurrence
    days_ahead = target_day - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    next_date = now + timedelta(days=days_ahead)
    next_datetime = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return next_datetime


async def get_next_sunday() -> str:
    """Вычисление даты следующего воскресенья"""
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        next_sunday = today + timedelta(days=7)
    else:
        next_sunday = today + timedelta(days=days_until_sunday)
    return next_sunday.strftime('%d.%m.%Y')


def format_date_with_weekday(date: datetime) -> str:
    """Форматирование даты с днём недели (например, '15.02.2026 (воскресенье)')"""
    formatted_date = date.strftime('%d.%m.%Y')
    weekday = get_weekday_russian(date)
    return f"{formatted_date} ({weekday})"
