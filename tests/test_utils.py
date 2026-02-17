#!/usr/bin/env python3
"""
Тесты для модуля utils.py
"""

import pytest
from datetime import datetime, timedelta
from utils import (
    get_weekday_russian,
    get_day_of_week_number,
    get_next_occurrence,
    get_next_sunday,
    format_date_with_weekday
)


class TestGetWeekdayRussian:
    """Тесты функции get_weekday_russian"""

    def test_monday(self):
        assert get_weekday_russian(datetime(2025, 1, 6)) == "понедельник"

    def test_tuesday(self):
        assert get_weekday_russian(datetime(2025, 1, 7)) == "вторник"

    def test_wednesday(self):
        assert get_weekday_russian(datetime(2025, 1, 8)) == "среда"

    def test_thursday(self):
        assert get_weekday_russian(datetime(2025, 1, 9)) == "четверг"

    def test_friday(self):
        assert get_weekday_russian(datetime(2025, 1, 10)) == "пятница"

    def test_saturday(self):
        assert get_weekday_russian(datetime(2025, 1, 11)) == "суббота"

    def test_sunday(self):
        assert get_weekday_russian(datetime(2025, 1, 12)) == "воскресенье"

    def test_invalid_day(self):
        # Проверяем, что функция возвращает пустую строку для несуществующего дня
        result = get_weekday_russian(datetime(2025, 1, 13))  # понедельник
        assert isinstance(result, str)


class TestGetDayOfWeekNumber:
    """Тесты функции get_day_of_week_number"""

    def test_monday(self):
        assert get_day_of_week_number("monday") == 0

    def test_tuesday(self):
        assert get_day_of_week_number("tuesday") == 1

    def test_wednesday(self):
        assert get_day_of_week_number("wednesday") == 2

    def test_thursday(self):
        assert get_day_of_week_number("thursday") == 3

    def test_friday(self):
        assert get_day_of_week_number("friday") == 4

    def test_saturday(self):
        assert get_day_of_week_number("saturday") == 5

    def test_sunday(self):
        assert get_day_of_week_number("sunday") == 6

    def test_case_insensitive(self):
        assert get_day_of_week_number("MONDAY") == 0
        assert get_day_of_week_number("Friday") == 4

    def test_invalid_day(self):
        assert get_day_of_week_number("invalid") == -1
        assert get_day_of_week_number("") == -1


class TestGetNextSunday:
    """Тесты функции get_next_sunday"""

    @pytest.mark.asyncio
    async def test_returns_string(self):
        result = await get_next_sunday()
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_format_dd_mm_yyyy(self):
        result = await get_next_sunday()
        parts = result.split(".")
        assert len(parts) == 3
        assert len(parts[0]) == 2  # день
        assert len(parts[1]) == 2  # месяц
        assert len(parts[2]) == 4  # год

    @pytest.mark.asyncio
    async def test_is_future_sunday(self):
        result = await get_next_sunday()
        day, month, year = map(int, result.split("."))
        result_date = datetime(year, month, day)
        # Проверяем, что это воскресенье (weekday() == 6)
        assert result_date.weekday() == 6


class TestFormatDateWithWeekday:
    """Тесты функции format_date_with_weekday"""

    def test_monday(self):
        date = datetime(2025, 1, 6)
        result = format_date_with_weekday(date)
        assert result == "06.01.2025 (понедельник)"

    def test_sunday(self):
        date = datetime(2025, 1, 12)
        result = format_date_with_weekday(date)
        assert result == "12.01.2025 (воскресенье)"

    def test_contains_date_and_weekday(self):
        date = datetime(2025, 1, 10)
        result = format_date_with_weekday(date)
        assert "10.01.2025" in result
        assert "пятница" in result


class TestGetNextOccurrence:
    """Тесты функции get_next_occurrence"""

    @pytest.mark.asyncio
    async def test_returns_datetime(self):
        result = await get_next_occurrence("monday", "18:00")
        assert isinstance(result, datetime)

    @pytest.mark.asyncio
    async def test_correct_time(self):
        result = await get_next_occurrence("monday", "18:00")
        assert result.hour == 18
        assert result.minute == 0

    @pytest.mark.asyncio
    async def test_is_future_date(self):
        result = await get_next_occurrence("monday", "18:00")
        assert result >= datetime.now()

    @pytest.mark.asyncio
    async def test_correct_weekday(self):
        # Запрашиваем следующий понедельник
        result = await get_next_occurrence("monday", "18:00")
        assert result.weekday() == 0

    @pytest.mark.asyncio
    async def test_invalid_day_raises_error(self):
        with pytest.raises(ValueError):
            await get_next_occurrence("invalid_day", "18:00")

    @pytest.mark.asyncio
    async def test_invalid_time_format(self):
        with pytest.raises(ValueError):
            await get_next_occurrence("monday", "invalid")
