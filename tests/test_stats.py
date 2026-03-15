#!/usr/bin/env python3
"""
Тесты для методов статистики тренировок
"""

import pytest
import os
import sqlite3
from datetime import datetime, timedelta
from database import Database


@pytest.fixture
def test_db():
    """Создание тестовой базы данных с таблицами для статистики"""
    db_path = "test_volleybot_stats.db"
    # Удаляем если существует
    if os.path.exists(db_path):
        os.remove(db_path)

    test_db = Database(db_path)
    test_db.create_tables()

    # Создаём дополнительные таблицы для тестов статистики
    cursor = test_db.conn.cursor()

    # Таблица events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            event_type TEXT NOT NULL,
            name TEXT NOT NULL,
            date DATE NOT NULL,
            start_time TEXT,
            end_time TEXT,
            location TEXT,
            chat_id TEXT,
            topic_id INTEGER,
            opponent TEXT,
            result TEXT,
            score TEXT,
            source_id TEXT,
            source_table TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица event_signups
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'registered',
            is_guest INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(event_id, user_id)
        )
    ''')

    # Таблица training_registrations (для обратной совместимости)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS training_registrations (
            id TEXT PRIMARY KEY,
            training_date DATE NOT NULL,
            training_time TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            topic_id INTEGER,
            user_telegram_id INTEGER NOT NULL,
            status TEXT DEFAULT 'registered',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(training_date, training_time, chat_id, user_telegram_id)
        )
    ''')

    test_db.conn.commit()
    yield test_db

    test_db.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def db_with_data(test_db):
    """База данных с тестовыми данными"""
    # Создаём тестовых пользователей
    test_db.add_user(telegram_id=111111111, first_name="User1", username="user1")
    test_db.add_user(telegram_id=222222222, first_name="User2", username="user2")
    test_db.add_user(telegram_id=333333333, first_name="User3", username="user3")
    
    # Создаём тестовую тренировку в events
    today = datetime.now().strftime('%Y-%m-%d')
    cursor = test_db.conn.cursor()

    # Добавляем тренировку
    cursor.execute('''
        INSERT INTO events (uuid, event_type, name, date, start_time, end_time, location, chat_id, source_id, source_table)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('test-uuid-1', 'training', 'Тренировка', today, '18:00', '20:00', 'ВГАФК', '-1001234567890', '1', 'one_time_trainings'))

    event_id = cursor.lastrowid

    # Получаем ID пользователей
    user1 = test_db.get_user_by_telegram_id(111111111)
    user2 = test_db.get_user_by_telegram_id(222222222)
    user3 = test_db.get_user_by_telegram_id(333333333)

    # Добавляем записи на тренировку
    cursor.execute('''
        INSERT INTO event_signups (event_id, user_id, status, is_guest)
        VALUES (?, ?, ?, ?)
    ''', (event_id, user1['id'], 'registered', 0))  # User1

    cursor.execute('''
        INSERT INTO event_signups (event_id, user_id, status, is_guest)
        VALUES (?, ?, ?, ?)
    ''', (event_id, user2['id'], 'registered', 0))  # User2

    cursor.execute('''
        INSERT INTO event_signups (event_id, user_id, status, is_guest)
        VALUES (?, ?, ?, ?)
    ''', (event_id, user3['id'], 'registered', 1))  # User3 как гость

    test_db.conn.commit()
    return test_db


class TestTrainingStats:
    """Тесты для get_training_stats"""

    def test_get_training_stats_empty(self, test_db):
        """Статистика для пустой базы"""
        stats = test_db.get_training_stats(period='week')
        assert stats is not None
        assert stats.get('total_trainings', 0) >= 0
    
    def test_get_training_stats_with_data(self, db_with_data):
        """Статистика с данными"""
        stats = db_with_data.get_training_stats(period='week')
        assert stats is not None
        assert 'total_trainings' in stats
        assert 'total_signups' in stats
        assert 'unique_users' in stats
        assert 'users_count' in stats
        assert 'guests_count' in stats
        assert 'avg_per_training' in stats
        assert 'date_range' in stats
        assert 'period' in stats
    
    def test_get_training_stats_periods(self, db_with_data):
        """Статистика для разных периодов"""
        for period in ['day', 'week', 'month', 'all']:
            stats = db_with_data.get_training_stats(period=period)
            assert stats is not None
            assert stats['period'] == period


class TestTrainingDetails:
    """Тесты для get_training_details"""

    def test_get_training_details_not_found(self, test_db):
        """Детали для несуществующей тренировки"""
        details = test_db.get_training_details('2099-01-01')
        assert 'error' in details
        assert details['error'] == 'Training not found'

    def test_get_training_details_with_data(self, db_with_data):
        """Детали тренировки с данными"""
        today = datetime.now().strftime('%Y-%m-%d')
        details = db_with_data.get_training_details(today)

        assert 'error' not in details
        assert 'training_info' in details
        assert 'participants' in details
        assert 'stats' in details

        stats = details['stats']
        assert 'total' in stats
        assert 'users_count' in stats
        assert 'guests_count' in stats

        # Проверяем что найдено 3 участника
        assert stats['total'] == 3
        assert stats['users_count'] == 2
        assert stats['guests_count'] == 1


class TestUserStats:
    """Тесты для get_user_stats"""

    def test_get_user_stats_not_found(self, test_db):
        """Статистика для несуществующего пользователя"""
        stats = test_db.get_user_stats(user_id=999999999)
        assert 'error' in stats
        assert stats['error'] == 'User not found'

    def test_get_user_stats_with_data(self, db_with_data):
        """Статистика пользователя с данными"""
        stats = db_with_data.get_user_stats(user_id=111111111, period='week')

        assert 'error' not in stats
        assert 'user_info' in stats
        assert 'stats' in stats
        assert 'period' in stats
        assert 'date_range' in stats

        user_stats = stats['stats']
        assert 'total_trainings' in user_stats
        assert 'attended_trainings' in user_stats
        assert 'waitlist_count' in user_stats
        assert 'guests_trainings' in user_stats


class TestTopUsers:
    """Тесты для get_top_users"""

    def test_get_top_users_empty(self, test_db):
        """Топ для пустой базы"""
        top = test_db.get_top_users(limit=10)
        assert top == []

    def test_get_top_users_with_data(self, db_with_data):
        """Топ пользователей с данными"""
        top = db_with_data.get_top_users(limit=10, period='week')

        assert isinstance(top, list)
        assert len(top) > 0

        # Проверяем структуру
        for user in top:
            assert 'telegram_id' in user
            assert 'first_name' in user
            assert 'total_trainings' in user
            assert 'attended_trainings' in user

    def test_get_top_users_limit(self, db_with_data):
        """Топ с ограничением"""
        for limit in [1, 5, 10]:
            top = db_with_data.get_top_users(limit=limit)
            assert len(top) <= limit


class TestPeriodHelpers:
    """Тесты для вспомогательных методов периодов"""

    def test_get_period_filter(self, test_db):
        """Фильтр периодов"""
        for period in ['day', 'week', 'month', 'all']:
            filter_str, params = test_db._get_period_filter(period)
            assert filter_str is not None
            assert isinstance(params, list)

    def test_get_period_date_range(self, test_db):
        """Диапазон дат периодов"""
        for period in ['day', 'week', 'month', 'all']:
            date_range = test_db._get_period_date_range(period)
            assert 'from' in date_range
            assert 'to' in date_range
