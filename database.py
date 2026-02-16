#!/usr/bin/env python3
"""
Модуль для работы с SQLite базой данных
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """
    Класс для работы с SQLite базой данных
    """

    def __init__(self, db_path: str = "volleybot.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Подключение к базе данных"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Подключено к базе данных: {self.db_path}")

    def _create_tables(self):
        """Создание таблиц если они не существуют"""
        cursor = self.conn.cursor()

        # Таблица настроек бота
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица расписаний опросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poll_schedules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                message_thread_id INTEGER,
                training_day TEXT NOT NULL,
                poll_day TEXT NOT NULL,
                training_time TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица активных опросов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_polls (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                message_thread_id INTEGER,
                template_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()
        logger.info("Таблицы базы данных созданы/проверены")

    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")

    # ==================== Методы для работы с настройками ====================

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получение настройки по ключу"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row is None:
            return default
        try:
            return json.loads(row['value'])
        except json.JSONDecodeError:
            return row['value']

    def set_setting(self, key: str, value: Any):
        """Сохранение настройки"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, json.dumps(value) if not isinstance(value, str) else value))
        self.conn.commit()

    def get_admin_ids(self) -> List[int]:
        """Получение списка ID администраторов"""
        admin_ids = self.get_setting('admin_user_ids', [])
        return [int(id) for id in admin_ids]

    def set_admin_ids(self, admin_ids: List[int]):
        """Сохранение списка ID администраторов"""
        self.set_setting('admin_user_ids', [int(id) for id in admin_ids])

    def add_admin_id(self, admin_id: int):
        """Добавление ID администратора"""
        admin_ids = self.get_admin_ids()
        if admin_id not in admin_ids:
            admin_ids.append(admin_id)
            self.set_admin_ids(admin_ids)

    def get_default_template(self) -> Dict[str, Any]:
        """Получение шаблона опроса по умолчанию"""
        default = {
            'name': 'Волейбольный опрос',
            'description': 'Волейбол {date} {time} ВГАФК',
            'training_day': 'sunday',
            'poll_day': 'friday',
            'training_time': '18:00',
            'options': ['Буду', 'Не буду', 'Возможно'],
            'enabled': True,
            'default_chat_id': '',
            'default_topic_id': None
        }
        stored = self.get_setting('default_poll_template', default)
        # Объединяем с дефолтными значениями на случай добавления новых полей
        if isinstance(stored, dict):
            default.update(stored)
        return default

    def set_default_template(self, template: Dict[str, Any]):
        """Сохранение шаблона опроса по умолчанию"""
        self.set_setting('default_poll_template', template)

    def update_template_field(self, field: str, value: Any):
        """Обновление отдельного поля шаблона"""
        template = self.get_default_template()
        template[field] = value
        self.set_default_template(template)

    # ==================== Методы для работы с расписаниями ====================

    def get_poll_schedules(self) -> List[Dict[str, Any]]:
        """Получение всех расписаний опросов"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM poll_schedules ORDER BY created_at')
        rows = cursor.fetchall()
        schedules = []
        for row in rows:
            schedule = dict(row)
            schedule['enabled'] = bool(schedule['enabled'])
            schedules.append(schedule)
        return schedules

    def add_poll_schedule(self, schedule: Dict[str, Any]):
        """Добавление расписания опроса"""
        cursor = self.conn.cursor()
        schedule_id = schedule.get('id', str(datetime.now().timestamp()))
        cursor.execute('''
            INSERT INTO poll_schedules (id, name, chat_id, message_thread_id, 
                                        training_day, poll_day, training_time, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            schedule_id,
            schedule.get('name', 'Расписание'),
            schedule['chat_id'],
            schedule.get('message_thread_id'),
            schedule['training_day'],
            schedule['poll_day'],
            schedule['training_time'],
            1 if schedule.get('enabled', True) else 0
        ))
        self.conn.commit()

    def update_poll_schedule(self, schedule_id: str, updates: Dict[str, Any]):
        """Обновление расписания опроса"""
        cursor = self.conn.cursor()
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [schedule_id]
        cursor.execute(f'''
            UPDATE poll_schedules 
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', values)
        self.conn.commit()

    def remove_poll_schedule(self, schedule_id: str):
        """Удаление расписания опроса"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM poll_schedules WHERE id = ?', (schedule_id,))
        self.conn.commit()

    def get_poll_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Получение расписания по ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM poll_schedules WHERE id = ?', (schedule_id,))
        row = cursor.fetchone()
        if row:
            schedule = dict(row)
            schedule['enabled'] = bool(schedule['enabled'])
            return schedule
        return None

    # ==================== Методы для работы с активными опросами ====================

    def add_active_poll(self, poll_id: str, chat_id: str, message_id: int, 
                        message_thread_id: Optional[int] = None, 
                        template_id: Optional[str] = None):
        """Добавление активного опроса"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO active_polls (id, chat_id, message_id, message_thread_id, template_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (poll_id, chat_id, message_id, message_thread_id, template_id))
        self.conn.commit()

    def get_active_polls(self) -> List[Dict[str, Any]]:
        """Получение всех активных опросов"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM active_polls ORDER BY created_at')
        rows = cursor.fetchall()
        polls = []
        for row in rows:
            poll = dict(row)
            polls.append(poll)
        return polls

    def remove_active_poll(self, poll_id: str):
        """Удаление активного опроса"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM active_polls WHERE id = ?', (poll_id,))
        self.conn.commit()

    def get_active_poll(self, poll_id: str) -> Optional[Dict[str, Any]]:
        """Получение активного опроса по ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM active_polls WHERE id = ?', (poll_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    # ==================== Методы миграции ====================

    def migrate_from_json(self, json_path: str = "data.json"):
        """Миграция данных из JSON файла в базу данных"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.info(f"Файл {json_path} не найден, миграция не требуется")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return False

        # Миграция администраторов
        admin_ids = data.get('admin', {}).get('user_ids', [])
        if admin_ids:
            self.set_admin_ids(admin_ids)
            logger.info(f"Мигрировано {len(admin_ids)} администраторов")

        # Миграция шаблона опроса
        template = data.get('default_poll_template', {})
        if template:
            self.set_default_template(template)
            logger.info("Мигрирован шаблон опроса по умолчанию")

        # Миграция расписаний
        schedules = data.get('poll_schedules', [])
        for schedule in schedules:
            self.add_poll_schedule(schedule)
        if schedules:
            logger.info(f"Мигрировано {len(schedules)} расписаний")

        # Миграция активных опросов
        active_polls = data.get('active_polls', {})
        for poll_id, poll_data in active_polls.items():
            self.add_active_poll(
                poll_id=poll_id,
                chat_id=poll_data.get('chat_id', ''),
                message_id=poll_data.get('message_id', 0),
                message_thread_id=poll_data.get('message_thread_id'),
                template_id=poll_data.get('template_id')
            )
        if active_polls:
            logger.info(f"Мигрировано {len(active_polls)} активных опросов")

        logger.info("Миграция данных из JSON завершена успешно")
        return True

    def is_initialized(self) -> bool:
        """Проверка, инициализирована ли база данных (есть ли администраторы)"""
        admin_ids = self.get_admin_ids()
        return len(admin_ids) > 0
