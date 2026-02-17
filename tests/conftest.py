#!/usr/bin/env python3
"""
Конфигурация и fixtures для тестов VolleyBot
"""

import pytest
import os
import tempfile
from pathlib import Path

# Добавляем корень проекта в path для импортов
PROJECT_ROOT = Path(__file__).parent.parent
os.sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def test_db_path():
    """Создание временной БД для тестов"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield db_path
    # Удаляем файл БД после тестов
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db():
    """Фикстура для Database с чистой БД для каждого теста"""
    from database import Database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(db_path)
    database.create_tables()
    yield database
    database.close()
    # Удаляем файл БД после теста
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db_with_admin():
    """Фикстура для Database с добавленным администратором"""
    from database import Database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database = Database(db_path)
    database.create_tables()
    database.add_admin_id(123456789)
    yield database
    database.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_schedule():
    """Пример расписания для тестов"""
    return {
        "id": "test-schedule-1",
        "name": "Тестовое расписание",
        "chat_id": "-1001234567890",
        "message_thread_id": None,
        "training_day": "sunday",
        "poll_day": "friday",
        "training_time": "18:00 - 20:00",
        "poll_time": "12:00",
        "enabled": True
    }


@pytest.fixture
def sample_template():
    """Пример шаблона опроса для тестов"""
    return {
        "name": "Волейбольный опрос",
        "description": "Волейбол {date} {time} ВГАФК",
        "training_day": "sunday",
        "poll_day": "friday",
        "training_time": "18:00 - 20:00",
        "options": ["Буду", "Не буду", "Возможно"],
        "enabled": True,
        "default_chat_id": "-1001234567890",
        "default_topic_id": None
    }
