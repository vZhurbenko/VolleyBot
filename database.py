#!/usr/bin/env python3
"""
Модуль для работы с SQLite базой данных
"""

import sqlite3
import json
import logging
import os
import sys
import uuid as uuid_module
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

    def _connect(self):
        """Подключение к базе данных"""
        # Не создаём файл если он не существует
        if not os.path.exists(self.db_path):
            logger.info(f"База данных не существует: {self.db_path}")
            return
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Подключено к базе данных: {self.db_path}")

    def create_tables(self):
        """Создание таблиц если они не существуют"""
        # Если БД не существует, создаём её
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Создана база данных: {self.db_path}")
        
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
                start_time TEXT,
                end_time TEXT,
                location TEXT,
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

        # Таблица пользователей для веб-авторизации
        # is_admin: пользователь является администратором
        # is_guest: пользователь является гостем (только для записи на тренировки)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT,
                username TEXT,
                photo_url TEXT,
                is_admin INTEGER DEFAULT 0,
                is_guest INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # Таблица игр
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                location TEXT,
                start_time TEXT,
                end_time TEXT,
                opponent TEXT,
                chat_id TEXT,
                topic_id INTEGER,
                result TEXT,
                score TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица гостей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT,
                username TEXT,
                photo_url TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица записей гостей на тренировки (множественная запись)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guest_signups (
                id TEXT PRIMARY KEY,
                user_telegram_id INTEGER NOT NULL,
                training_uuid TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_telegram_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (training_uuid) REFERENCES games(uuid) ON DELETE CASCADE
            )
        ''')

        # Индексы для guest_signups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_guest_signups_telegram
            ON guest_signups(user_telegram_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_guest_signups_training
            ON guest_signups(training_uuid)
        ''')
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_guest_signups_unique
            ON guest_signups(user_telegram_id, training_uuid)
        ''')

        # Таблица записей на игры
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_signups (
                id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                user_telegram_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'registered',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
                FOREIGN KEY (user_telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
            )
        ''')

        # Таблица регулярных тренировок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_trainings (
                id TEXT PRIMARY KEY,
                uuid TEXT UNIQUE,
                schedule_id TEXT NOT NULL,
                training_date DATE NOT NULL,
                training_time TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                chat_id TEXT NOT NULL,
                topic_id INTEGER,
                name TEXT,
                location TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (schedule_id) REFERENCES poll_schedules(id) ON DELETE CASCADE
            )
        ''')

        # Таблица разовых тренировок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS one_time_trainings (
                id TEXT PRIMARY KEY,
                uuid TEXT UNIQUE,
                training_date DATE NOT NULL,
                training_time TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                chat_id TEXT NOT NULL,
                topic_id INTEGER,
                name TEXT,
                location TEXT,
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
        if not self.conn:
            return default
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
        if not self.conn:
            logger.error(f"Нельзя сохранить настройку {key}: база данных не подключена")
            return
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, json.dumps(value) if not isinstance(value, str) else value))
        self.conn.commit()

    def get_admin_ids(self) -> List[int]:
        """Получение списка ID администраторов из таблицы users"""
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT telegram_id FROM users WHERE is_admin = 1')
        return [row['telegram_id'] for row in cursor.fetchall()]

    def set_admin_ids(self, admin_ids: List[int]):
        """Установка списка ID администраторов (полная замена)"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # Снимаем статус админа со всех
        cursor.execute('UPDATE users SET is_admin = 0')
        
        # Устанавливаем статус админа указанным пользователям
        for admin_id in admin_ids:
            cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, first_name, is_admin) 
                VALUES (?, ?, 1)
                ON CONFLICT(telegram_id) DO UPDATE SET is_admin = 1, updated_at = CURRENT_TIMESTAMP
            ''', (admin_id, f'Admin {admin_id}'))
        
        self.conn.commit()

    def add_admin_id(self, admin_id: int):
        """Добавление ID администратора"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, first_name, is_admin) 
            VALUES (?, ?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET is_admin = 1, updated_at = CURRENT_TIMESTAMP
        ''', (admin_id, f'Admin {admin_id}'))
        self.conn.commit()

    def remove_admin_id(self, admin_id: int):
        """Удаление ID администратора"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_admin = 0, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?', (admin_id,))
        self.conn.commit()

    def update_user_admin_status(self, telegram_id: int, is_admin: bool):
        """Обновление статуса администратора пользователя"""
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE users SET is_admin = ? WHERE telegram_id = ?',
                          (1 if is_admin else 0, telegram_id))
            self.conn.commit()

    def get_default_template(self) -> Dict[str, Any]:
        """Получение шаблона опроса по умолчанию"""
        default = {
            'name': 'Волейбольная тренировка',
            'description': '{name} {date} {start_time} - {end_time} {location}',
            'training_day': 'sunday',
            'start_time': '18:00',
            'end_time': '20:00',
            'location': 'ВГАФК',
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
        if not self.conn:
            return []
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
        if not self.conn:
            logger.error("Нельзя добавить расписание: база данных не подключена")
            return
        cursor = self.conn.cursor()
        schedule_id = schedule.get('id', str(datetime.now().timestamp()))
        cursor.execute('''
            INSERT INTO poll_schedules (id, name, chat_id, message_thread_id,
                                        training_day, start_time, end_time, location, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            schedule_id,
            schedule.get('name', 'Расписание'),
            schedule['chat_id'],
            schedule.get('message_thread_id'),
            schedule['training_day'],
            schedule.get('start_time'),
            schedule.get('end_time'),
            schedule.get('location', 'ВГАФК'),
            1 if schedule.get('enabled', True) else 0
        ))
        self.conn.commit()

    def update_poll_schedule(self, schedule_id: str, updates: Dict[str, Any]):
        """Обновление расписания опроса"""
        if not self.conn:
            logger.error("Нельзя обновить расписание: база данных не подключена")
            return
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
        if not self.conn:
            logger.error("Нельзя удалить расписание: база данных не подключена")
            return
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM poll_schedules WHERE id = ?', (schedule_id,))
        self.conn.commit()

    def get_poll_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Получение расписания по ID"""
        if not self.conn:
            return None
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
                        template_id: Optional[str] = None,
                        name: Optional[str] = None,
                        training_date: Optional[str] = None,
                        training_time: Optional[str] = None,
                        location: Optional[str] = None):
        """Добавление активного опроса"""
        if not self.conn:
            logger.error("Нельзя добавить активный опрос: база данных не подключена")
            return
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO active_polls (id, chat_id, message_id, message_thread_id, template_id,
                                       name, training_date, training_time, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (poll_id, chat_id, message_id, message_thread_id, template_id,
              name, training_date, training_time, location))
        self.conn.commit()

    def get_active_polls(self) -> List[Dict[str, Any]]:
        """Получение всех активных опросов"""
        if not self.conn:
            return []
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
        if not self.conn:
            logger.error("Нельзя удалить активный опрос: база данных не подключена")
            return
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM active_polls WHERE id = ?', (poll_id,))
        self.conn.commit()

    def get_active_poll(self, poll_id: str) -> Optional[Dict[str, Any]]:
        """Получение активного опроса по ID"""
        if not self.conn:
            return None
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM active_polls WHERE id = ?', (poll_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    # ==================== Методы миграции ====================

    def migrate_games_uuid(self) -> Dict[str, Any]:
        """
        Миграция: добавление UUID для существующих записей в таблице games
        
        Returns:
            Dict с результатом миграции (количество обновлённых записей)
        """
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        try:
            # Находим записи без UUID
            cursor.execute('''
                SELECT id FROM games WHERE uuid IS NULL
            ''')
            games_without_uuid = cursor.fetchall()
            
            updated_count = 0
            for game in games_without_uuid:
                game_id = game['id']
                new_uuid = str(uuid_module.uuid4())
                cursor.execute('''
                    UPDATE games SET uuid = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                ''', (new_uuid, game_id))
                updated_count += 1
            
            self.conn.commit()
            logger.info(f"Миграция UUID завершена: обновлено {updated_count} записей")
            return {"success": True, "updated_count": updated_count}
        except Exception as e:
            logger.error(f"Ошибка миграции UUID: {e}")
            return {"success": False, "error": str(e)}

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

    # ==================== Методы для работы с пользователями (web auth) ====================

    def add_user(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        photo_url: Optional[str] = None,
        is_admin: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Добавление нового пользователя"""
        if not self.conn:
            logger.error("Нельзя добавить пользователя: база данных не подключена")
            return None

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, username, photo_url, is_admin, is_active, last_login)
                VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ''', (
                telegram_id,
                first_name,
                last_name,
                username,
                photo_url,
                1 if is_admin else 0
            ))
            self.conn.commit()
            logger.info(f"Пользователь добавлен: {telegram_id}")
            return self.get_user_by_telegram_id(telegram_id)
        except sqlite3.IntegrityError:
            logger.warning(f"Пользователь {telegram_id} уже существует")
            return None

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по Telegram ID"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()

        if row:
            user = dict(row)
            user['is_admin'] = bool(user['is_admin'])
            user['is_guest'] = bool(user.get('is_guest', 0))
            user['is_active'] = bool(user.get('is_active', 1))
            return user
        return None

    def update_user(
        self,
        telegram_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Обновление данных пользователя"""
        if not self.conn:
            logger.error("Нельзя обновить пользователя: база данных не подключена")
            return None

        updates = []
        values = []

        if first_name is not None:
            updates.append("first_name = ?")
            values.append(first_name)
        if last_name is not None:
            updates.append("last_name = ?")
            values.append(last_name)
        if username is not None:
            updates.append("username = ?")
            values.append(username)
        if photo_url is not None:
            updates.append("photo_url = ?")
            values.append(photo_url)

        if not updates:
            return self.get_user_by_telegram_id(telegram_id)

        updates.append("updated_at = CURRENT_TIMESTAMP")
        updates.append("last_login = CURRENT_TIMESTAMP")
        values.append(telegram_id)

        cursor = self.conn.cursor()
        cursor.execute(f'''
            UPDATE users
            SET {', '.join(updates)}
            WHERE telegram_id = ?
        ''', values)
        self.conn.commit()

        return self.get_user_by_telegram_id(telegram_id)

    def set_user_admin(self, telegram_id: int, is_admin: bool) -> Dict[str, Any]:
        """Установка/снятие статуса администратора пользователя"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            cursor.execute(
                'UPDATE users SET is_admin = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?',
                (1 if is_admin else 0, telegram_id)
            )
            self.conn.commit()

            return {"success": True, "message": f"Статус администратора {'установлен' if is_admin else 'снят'}"}
        except Exception as e:
            logger.error(f"Ошибка установки статуса админа: {e}")
            return {"success": False, "error": str(e)}

    def get_all_users(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получение всех пользователей с опциональной фильтрацией

        Args:
            filter_type: Тип фильтрации:
                - None: все пользователи
                - 'active': активные пользователи (is_active = 1)
                - 'inactive': неактивные пользователи (is_active = 0)
                - 'guests': гости (is_guest = 1)

        Returns:
            Список пользователей с применённым фильтром
        """
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Формируем SQL-запрос с фильтром
        if filter_type == 'active':
            cursor.execute('SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC')
        elif filter_type == 'inactive':
            cursor.execute('SELECT * FROM users WHERE is_active = 0 ORDER BY created_at DESC')
        elif filter_type == 'guests':
            cursor.execute('SELECT * FROM users WHERE is_guest = 1 ORDER BY created_at DESC')
        else:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')

        rows = cursor.fetchall()

        users = []
        for row in rows:
            user = dict(row)
            user['is_admin'] = bool(user['is_admin'])
            user['is_active'] = bool(user['is_active']) if 'is_active' in user else True
            # Проверяем является ли пользователь гостем
            user['is_guest'] = self.is_guest(user['telegram_id'])
            users.append(user)

        return users

    def get_admin_count(self) -> int:
        """Получение количества администраторов"""
        if not self.conn:
            return 0

        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
        return cursor.fetchone()[0]

    # ==================== Методы для работы с тренировками ====================

    def get_training_registrations(self, training_date: str, training_time: str, chat_id: str) -> List[Dict[str, Any]]:
        """Получение всех записей на тренировку (из training_registrations + guest_signups)"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Получаем UUID тренировки по дате, времени и chat_id
        cursor.execute('''
            SELECT uuid FROM one_time_trainings
            WHERE training_date = ? AND training_time = ? AND chat_id = ?
            LIMIT 1
        ''', (training_date, training_time, chat_id))
        row = cursor.fetchone()

        training_uuid = row['uuid'] if row else None

        # Если тренировка не найдена, пробуем scheduled_trainings
        if not training_uuid:
            cursor.execute('''
                SELECT uuid FROM scheduled_trainings
                WHERE training_date = ? AND training_time = ? AND chat_id = ?
                LIMIT 1
            ''', (training_date, training_time, chat_id))
            row = cursor.fetchone()
            training_uuid = row['uuid'] if row else None

        # Если UUID не найден, возвращаем пустой список
        if not training_uuid:
            return []

        # Получаем участников из guest_signups (новая архитектура)
        cursor.execute('''
            SELECT
                u.telegram_id as user_telegram_id,
                gs.created_at as registered_at,
                u.first_name,
                u.last_name,
                u.username,
                u.photo_url,
                u.is_admin,
                u.is_guest,
                'registered' as status
            FROM guest_signups gs
            JOIN users u ON gs.user_telegram_id = u.id
            WHERE gs.training_uuid = ? AND u.is_active = 1
            ORDER BY gs.created_at ASC
        ''', (training_uuid,))

        rows = [dict(row) for row in cursor.fetchall()]
        # Преобразуем поля в bool
        for row in rows:
            if 'is_admin' in row:
                row['is_admin'] = bool(row['is_admin'])
            if 'is_guest' in row:
                row['is_guest'] = bool(row['is_guest'])
        return rows

    def get_training_registrations_by_uuid(self, training_uuid: str) -> List[Dict[str, Any]]:
        """Получение всех записей на тренировку по UUID (из training_registrations)"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Получаем дату, время и chat_id по UUID
        cursor.execute('''
            SELECT training_date, training_time, chat_id FROM one_time_trainings
            WHERE uuid = ?
            LIMIT 1
        ''', (training_uuid,))
        row = cursor.fetchone()

        if not row:
            # Пробуем scheduled_trainings
            cursor.execute('''
                SELECT training_date, training_time, chat_id FROM scheduled_trainings
                WHERE uuid = ?
                LIMIT 1
            ''', (training_uuid,))
            row = cursor.fetchone()

        if not row:
            return []

        training_date = row['training_date']
        training_time = row['training_time']
        chat_id = row['chat_id']

        # Получаем участников из training_registrations
        cursor.execute('''
            SELECT
                tr.user_telegram_id,
                tr.registered_at,
                u.first_name,
                u.last_name,
                u.username,
                u.photo_url,
                u.is_admin,
                u.is_guest,
                tr.status
            FROM training_registrations tr
            JOIN users u ON tr.user_telegram_id = u.id
            WHERE tr.training_date = ? AND tr.training_time = ? AND tr.chat_id = ?
              AND u.is_active = 1
            ORDER BY tr.registered_at ASC
        ''', (training_date, training_time, chat_id))

        rows = [dict(row) for row in cursor.fetchall()]
        # Преобразуем поля в bool
        for row in rows:
            if 'is_admin' in row:
                row['is_admin'] = bool(row['is_admin'])
            if 'is_guest' in row:
                row['is_guest'] = bool(row['is_guest'])
        return rows

    def register_for_training(self, training_id: str, training_date: str, training_time: str,
                              chat_id: str, topic_id: Optional[int], user_telegram_id: int) -> Dict[str, Any]:
        """Запись на тренировку с проверкой лимита (12 человек) + дублирование в event_signups"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        # Считаем сколько уже записано со статусом 'registered'
        cursor.execute('''
            SELECT COUNT(*) as count FROM training_registrations
            WHERE training_date = ? AND training_time = ? AND chat_id = ? AND status = 'registered'
        ''', (training_date, training_time, chat_id))

        result = cursor.fetchone()
        registered_count = result['count'] if result else 0

        # Определяем статус
        if registered_count < 12:
            status = 'registered'
        else:
            status = 'waitlist'

        try:
            # Проверяем, есть ли уже запись этого пользователя
            cursor.execute('''
                SELECT id, status FROM training_registrations
                WHERE training_date = ? AND training_time = ? AND chat_id = ? AND user_telegram_id = ?
            ''', (training_date, training_time, chat_id, user_telegram_id))

            existing = cursor.fetchone()

            if existing:
                # Обновляем существующую запись
                cursor.execute('''
                    UPDATE training_registrations
                    SET status = ?, topic_id = ?, registered_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, topic_id, existing['id']))
            else:
                # Создаём новую запись
                cursor.execute('''
                    INSERT INTO training_registrations
                    (id, training_date, training_time, chat_id, topic_id, user_telegram_id, status, registered_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (training_id, training_date, training_time, chat_id, topic_id, user_telegram_id, status))

            # НАХОДИМ event по uuid (для дублирования в event_signups)
            # Извлекаем start_time из training_time (формат: "HH:MM - HH:MM" или "HH:MM")
            start_time = training_time.split(' - ')[0] if ' - ' in training_time else training_time
            
            cursor.execute('''
                SELECT id FROM events
                WHERE source_table IN ('scheduled_trainings', 'one_time_trainings')
                  AND date = ? AND start_time = ? AND chat_id = ?
                LIMIT 1
            ''', (training_date, start_time, chat_id))
            
            event_row = cursor.fetchone()
            if event_row:
                event_id = dict(event_row)['id']

                # Получаем user_id
                cursor.execute('SELECT id, is_guest FROM users WHERE telegram_id = ?', (user_telegram_id,))
                user_row = cursor.fetchone()
                if user_row:
                    user_row_dict = dict(user_row)
                    user_id = user_row_dict['id']
                    is_guest = bool(user_row_dict.get('is_guest', 0))

                    # Проверяем существующую запись в event_signups
                    cursor.execute('''
                        SELECT id, status FROM event_signups
                        WHERE event_id = ? AND user_id = ?
                    ''', (event_id, user_id))

                    event_signup = cursor.fetchone()
                    if event_signup:
                        event_signup_dict = dict(event_signup)
                        # Обновляем статус
                        cursor.execute('''
                            UPDATE event_signups
                            SET status = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (status, event_signup_dict['id']))
                    else:
                        # Создаём новую запись
                        cursor.execute('''
                            INSERT INTO event_signups (event_id, user_id, status, is_guest, created_at)
                            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (event_id, user_id, status, 1 if is_guest else 0))

            self.conn.commit()

            return {"success": True, "status": status}
        except Exception as e:
            logger.error(f"Ошибка записи на тренировку: {e}")
            return {"success": False, "error": str(e)}

    def unregister_from_training(self, training_date: str, training_time: str,
                                 chat_id: str, user_telegram_id: int) -> Dict[str, Any]:
        """Отписка от тренировки с автоматическим зачислением из waitlist + удаление из event_signups"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Удаляем запись из training_registrations
            cursor.execute('''
                DELETE FROM training_registrations
                WHERE training_date = ? AND training_time = ? AND chat_id = ? AND user_telegram_id = ?
            ''', (training_date, training_time, chat_id, user_telegram_id))

            # НАХОДИМ event для удаления из event_signups
            cursor.execute('''
                SELECT id FROM events
                WHERE source_table IN ('scheduled_trainings', 'one_time_trainings')
                  AND date = ? AND start_time = ? AND chat_id = ?
                LIMIT 1
            ''', (training_date, training_time, chat_id))
            
            event_row = cursor.fetchone()
            if event_row:
                event_id = dict(event_row)['id']

                # Получаем user_id
                cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_telegram_id,))
                user_row = cursor.fetchone()
                if user_row:
                    user_id = dict(user_row)['id']

                    # Удаляем из event_signups
                    cursor.execute('''
                        DELETE FROM event_signups
                        WHERE event_id = ? AND user_id = ?
                    ''', (event_id, user_id))
            
            # Также удаляем из guest_signups (для обратной совместимости)
            cursor.execute('''
                DELETE FROM guest_signups
                WHERE user_telegram_id = (SELECT id FROM users WHERE telegram_id = ?)
                  AND training_uuid = (
                    SELECT uuid FROM events 
                    WHERE source_table IN ('scheduled_trainings', 'one_time_trainings')
                      AND date = ? AND start_time = ? AND chat_id = ?
                    LIMIT 1
                  )
            ''', (user_telegram_id, training_date, training_time, chat_id))

            self.conn.commit()

            # Находим первого в waitlist и переводим в registered
            cursor.execute('''
                SELECT id FROM training_registrations
                WHERE training_date = ? AND training_time = ? AND chat_id = ? AND status = 'waitlist'
                ORDER BY registered_at ASC
                LIMIT 1
            ''', (training_date, training_time, chat_id))

            waitlist_user = cursor.fetchone()
            if waitlist_user:
                cursor.execute('''
                    UPDATE training_registrations
                    SET status = 'registered'
                    WHERE id = ?
                ''', (waitlist_user['id'],))
                self.conn.commit()

            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка отписки от тренировки: {e}")
            return {"success": False, "error": str(e)}

    def admin_remove_user_from_training(self, training_date: str, training_time: str,
                                        chat_id: str, user_telegram_id: int) -> Dict[str, Any]:
        """Удаление участника из тренировки администратором с автоматическим зачислением из waitlist"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Проверяем существование записи
            cursor.execute('''
                SELECT id, status FROM training_registrations
                WHERE training_date = ? AND training_time = ? AND chat_id = ? AND user_telegram_id = ?
            ''', (training_date, training_time, chat_id, user_telegram_id))

            existing = cursor.fetchone()
            if not existing:
                return {"success": False, "error": "Запись не найдена"}

            # Удаляем запись
            cursor.execute('''
                DELETE FROM training_registrations
                WHERE training_date = ? AND training_time = ? AND chat_id = ? AND user_telegram_id = ?
            ''', (training_date, training_time, chat_id, user_telegram_id))

            self.conn.commit()

            # Находим первого в waitlist и переводим в registered
            cursor.execute('''
                SELECT id FROM training_registrations
                WHERE training_date = ? AND training_time = ? AND chat_id = ? AND status = 'waitlist'
                ORDER BY registered_at ASC
                LIMIT 1
            ''', (training_date, training_time, chat_id))

            waitlist_user = cursor.fetchone()
            if waitlist_user:
                cursor.execute('''
                    UPDATE training_registrations
                    SET status = 'registered'
                    WHERE id = ?
                ''', (waitlist_user['id'],))
                self.conn.commit()

            return {"success": True, "removed_status": existing['status']}
        except Exception as e:
            logger.error(f"Ошибка удаления участника из тренировки: {e}")
            return {"success": False, "error": str(e)}

    def get_user_trainings(self, user_telegram_id: int) -> List[Dict[str, Any]]:
        """Получение всех записей пользователя на тренировки (из event_signups + training_registrations)"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        # Сначала получаем из event_signups (новая архитектура)
        cursor.execute('''
            SELECT 
                e.date as training_date,
                e.start_time as training_time,
                e.end_time,
                e.name as training_name,
                e.location,
                e.chat_id,
                e.topic_id,
                e.uuid,
                es.status,
                es.created_at as registered_at,
                es.is_guest
            FROM event_signups es
            INNER JOIN events e ON es.event_id = e.id
            INNER JOIN users u ON es.user_id = u.id
            WHERE u.telegram_id = ? AND e.event_type IN ('training', 'scheduled_training', 'one_time_training')
            ORDER BY e.date ASC, e.start_time ASC
        ''', (user_telegram_id,))
        
        rows = cursor.fetchall()
        
        # Дополняем из training_registrations (старая архитектура)
        cursor.execute('''
            SELECT tr.*,
                   tr.training_date,
                   ot.name as training_name,
                   ot.location,
                   ps.name as schedule_name,
                   0 as is_guest
            FROM training_registrations tr
            LEFT JOIN one_time_trainings ot
                ON tr.training_date = ot.training_date
                AND tr.training_time = ot.training_time
                AND tr.chat_id = ot.chat_id
            LEFT JOIN poll_schedules ps
                ON tr.chat_id = ps.chat_id
                AND tr.training_time = (ps.start_time || ' - ' || ps.end_time)
            WHERE tr.user_telegram_id = ?
              AND tr.registered_at > (SELECT COALESCE(MAX(created_at), 0) FROM event_signups)
            ORDER BY tr.training_date ASC, tr.training_time ASC
        ''', (user_telegram_id,))
        
        rows.extend([dict(row) for row in cursor.fetchall()])
        
        return [dict(row) for row in rows]

    def add_one_time_training(self, training_id: str, training_date: str, training_time: str,
                              chat_id: str, topic_id: Optional[int], name: str,
                              start_time: Optional[str] = None, end_time: Optional[str] = None,
                              location: Optional[str] = None) -> Dict[str, Any]:
        """Добавление разовой тренировки + создание в events"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            import uuid as uuid_module
            training_uuid = str(uuid_module.uuid4())

            # Создаём в one_time_trainings
            cursor.execute('''
                INSERT INTO one_time_trainings (id, uuid, training_date, training_time, chat_id, topic_id, name, start_time, end_time, location, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (training_id, training_uuid, training_date, training_time, chat_id, topic_id, name, start_time, end_time, location))

            # Создаём в events
            cursor.execute('''
                INSERT INTO events (uuid, event_type, name, date, start_time, end_time, location, chat_id, topic_id, source_id, source_table, created_at)
                VALUES (?, 'one_time_training', ?, ?, ?, ?, ?, ?, ?, ?, 'one_time_trainings', CURRENT_TIMESTAMP)
            ''', (training_uuid, name, training_date, start_time, end_time, location, chat_id, topic_id, training_id))

            self.conn.commit()
            return {"success": True, "uuid": training_uuid}
        except Exception as e:
            logger.error(f"Ошибка добавления разовой тренировки: {e}")
            return {"success": False, "error": str(e)}

    def remove_one_time_training(self, training_id: str) -> Dict[str, Any]:
        """Удаление разовой тренировки"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Сначала находим тренировку по ID чтобы получить training_time
            cursor.execute('''
                SELECT training_date, training_time, chat_id FROM one_time_trainings WHERE id = ?
            ''', (training_id,))
            training = cursor.fetchone()
            
            if not training:
                return {"success": False, "error": "Тренировка не найдена"}
            
            training_date = training['training_date']
            training_time = training['training_time']
            chat_id = training['chat_id']

            # Сначала удаляем все записи на эту тренировку
            cursor.execute('''
                DELETE FROM training_registrations
                WHERE training_date = ? AND training_time = ? AND chat_id = ?
            ''', (training_date, training_time, chat_id))

            # Удаляем саму тренировку
            cursor.execute('DELETE FROM one_time_trainings WHERE id = ?', (training_id,))

            self.conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка удаления разовой тренировки: {e}")
            return {"success": False, "error": str(e)}

    def get_one_time_trainings(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Получение всех разовых тренировок за месяц"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM one_time_trainings
            WHERE strftime('%Y', training_date) = ? AND strftime('%m', training_date) = ?
            ORDER BY training_date ASC
        ''', (str(year), str(month).zfill(2)))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_scheduled_trainings(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Получение всех тренировок из расписаний за месяц"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT st.*, ps.name as schedule_name
            FROM scheduled_trainings st
            LEFT JOIN poll_schedules ps ON st.schedule_id = ps.id
            WHERE strftime('%Y', st.training_date) = ? AND strftime('%m', st.training_date) = ?
            ORDER BY st.training_date ASC
        ''', (str(year), str(month).zfill(2)))

        return [dict(row) for row in cursor.fetchall()]

    def add_scheduled_training(self, training_id: str, schedule_id: str, training_date: str,
                               training_time: str, chat_id: str, topic_id: Optional[int] = None,
                               name: str = '', start_time: Optional[str] = None,
                               end_time: Optional[str] = None,
                               location: Optional[str] = None) -> Dict[str, Any]:
        """Добавление тренировки из расписания в календарь"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            import uuid as uuid_module
            training_uuid = str(uuid_module.uuid4())
            
            cursor.execute('''
                INSERT INTO scheduled_trainings
                (id, uuid, schedule_id, training_date, training_time, start_time, end_time,
                 chat_id, topic_id, name, location, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (training_id, training_uuid, schedule_id, training_date, training_time,
                  start_time, end_time, chat_id, topic_id, name, location))

            self.conn.commit()
            return {"success": True, "uuid": training_uuid}
        except Exception as e:
            logger.error(f"Ошибка добавления тренировки из расписания: {e}")
            return {"success": False, "error": str(e)}

    def remove_scheduled_training(self, training_id: str) -> Dict[str, Any]:
        """Удаление тренировки из расписания"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            cursor.execute('DELETE FROM scheduled_trainings WHERE id = ?', (training_id,))
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка удаления тренировки из расписания: {e}")
            return {"success": False, "error": str(e)}

    def get_scheduled_training(self, training_id: str) -> Optional[Dict[str, Any]]:
        """Получение тренировки из расписания по ID"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM scheduled_trainings WHERE id = ?', (training_id,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def get_scheduled_training_by_schedule_and_date(self, schedule_id: str,
                                                     training_date: str) -> Optional[Dict[str, Any]]:
        """Проверка: существует ли уже тренировка из расписания на эту дату"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM scheduled_trainings
            WHERE schedule_id = ? AND training_date = ?
        ''', (schedule_id, training_date))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_trainings(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Получение всех записей на тренировки за период (для админа) - из event_signups + training_registrations"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        # Сначала получаем из event_signups (новая архитектура)
        cursor.execute('''
            SELECT 
                e.date as training_date,
                e.start_time as training_time,
                e.end_time,
                e.chat_id,
                e.topic_id,
                e.name as training_name,
                e.location,
                es.status,
                es.created_at as registered_at,
                u.first_name,
                u.last_name,
                u.username,
                NULL as schedule_name,
                es.is_guest
            FROM event_signups es
            INNER JOIN events e ON es.event_id = e.id
            INNER JOIN users u ON es.user_id = u.id
            WHERE e.event_type IN ('training', 'scheduled_training', 'one_time_training')
              AND e.date BETWEEN ? AND ?
              AND u.is_active = 1
            ORDER BY e.date ASC, e.start_time ASC, es.created_at ASC
        ''', (start_date, end_date))
        
        rows = [dict(row) for row in cursor.fetchall()]
        
        # Дополняем из training_registrations (старая архитектура)
        cursor.execute('''
            SELECT tr.*, u.first_name, u.last_name, u.username,
                   ot.name as training_name,
                   ot.location as location,
                   ps.name as schedule_name,
                   0 as is_guest
            FROM training_registrations tr
            LEFT JOIN users u ON tr.user_telegram_id = u.telegram_id
            LEFT JOIN one_time_trainings ot
                ON tr.training_date = ot.training_date
                AND tr.training_time = ot.training_time
                AND tr.chat_id = ot.chat_id
            LEFT JOIN poll_schedules ps
                ON tr.chat_id = ps.chat_id
                AND tr.training_time = (ps.start_time || ' - ' || ps.end_time)
            WHERE tr.training_date BETWEEN ? AND ?
              AND tr.registered_at > (SELECT COALESCE(MAX(created_at), 0) FROM event_signups)
            ORDER BY tr.training_date ASC, tr.training_time ASC, tr.registered_at ASC
        ''', (start_date, end_date))
        
        rows.extend([dict(row) for row in cursor.fetchall()])
        
        return rows

    def get_all_game_signups(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Получение всех записей на игры за период (для админа) - из event_signups + game_signups"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        # Сначала получаем из event_signups (новая архитектура)
        cursor.execute('''
            SELECT 
                e.name as game_name,
                e.date,
                e.location,
                e.start_time,
                e.opponent,
                es.status,
                es.created_at,
                u.first_name,
                u.last_name,
                u.username,
                es.is_guest
            FROM event_signups es
            INNER JOIN events e ON es.event_id = e.id
            INNER JOIN users u ON es.user_id = u.id
            WHERE e.event_type = 'game'
              AND e.date BETWEEN ? AND ?
              AND u.is_active = 1
            ORDER BY e.date ASC, e.start_time ASC, es.created_at ASC
        ''', (start_date, end_date))
        
        rows = [dict(row) for row in cursor.fetchall()]
        
        # Дополняем из game_signups (старая архитектура)
        cursor.execute('''
            SELECT gs.*, u.first_name, u.last_name, u.username,
                   g.name as game_name, g.date, g.location, g.start_time, g.opponent,
                   0 as is_guest
            FROM game_signups gs
            LEFT JOIN users u ON gs.user_telegram_id = u.telegram_id
            LEFT JOIN games g ON gs.game_id = g.id
            WHERE g.date BETWEEN ? AND ?
              AND gs.created_at > (SELECT COALESCE(MAX(created_at), 0) FROM event_signups)
            ORDER BY g.date ASC, g.start_time ASC, gs.created_at ASC
        ''', (start_date, end_date))
        
        rows.extend([dict(row) for row in cursor.fetchall()])
        
        return rows

    # ==================== Методы для работы с пользователями (admin) ====================

    def get_all_web_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей веб-интерфейса"""
        if not self.conn:
            return []

        print("DEBUG: get_all_web_users called!", file=sys.stderr)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, telegram_id, first_name, last_name, username, photo_url, is_admin, is_active, last_login, created_at, updated_at FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()

        users = []
        for row in rows:
            user = {
                'id': row['id'],
                'telegram_id': row['telegram_id'],
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'username': row['username'],
                'photo_url': row['photo_url'],
                'is_admin': bool(row['is_admin']),
                'is_active': bool(row['is_active']),
                'last_login': row['last_login']
            }
            print(f"DEBUG: user {user['telegram_id']} is_active={user['is_active']}", file=sys.stderr)
            users.append(user)

        print(f"DEBUG: returning {len(users)} users", file=sys.stderr)
        self.conn.row_factory = None
        return users

    def add_web_user_by_telegram_id(self, telegram_id: int) -> Dict[str, Any]:
        """Добавление пользователя по Telegram ID (админ добавляет)"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        
        # Проверяем существует ли уже
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Активируем если был деактивирован
            cursor.execute('UPDATE users SET is_active = 1 WHERE telegram_id = ?', (telegram_id,))
            self.conn.commit()
            return {"success": True, "message": "Пользователь активирован", "user": dict(existing)}
        
        # Получаем данные через Telegram API (если бот может)
        # Для простоты создаём с минимальными данными
        try:
            cursor.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, username, is_admin, is_active, created_at)
                VALUES (?, ?, ?, ?, 0, 1, CURRENT_TIMESTAMP)
            ''', (telegram_id, f'User{telegram_id}', '', ''))
            
            self.conn.commit()
            
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = dict(cursor.fetchone())
            user['is_admin'] = bool(user['is_admin'])
            
            return {"success": True, "message": "Пользователь добавлен", "user": user}
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return {"success": False, "error": str(e)}

    def remove_web_user(self, telegram_id: int) -> Dict[str, Any]:
        """Удаление (деактивация) пользователя"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Деактивируем пользователя
            cursor.execute('UPDATE users SET is_active = 0 WHERE telegram_id = ?', (telegram_id,))
            self.conn.commit()

            return {"success": True, "message": "Пользователь деактивирован"}
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return {"success": False, "error": str(e)}

    def delete_web_user(self, telegram_id: int) -> Dict[str, Any]:
        """Полное удаление пользователя из БД"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Сначала удаляем все записи на тренировки
            self.remove_user_from_all_trainings(telegram_id)

            # Удаляем пользователя
            cursor.execute('DELETE FROM users WHERE telegram_id = ?', (telegram_id,))
            self.conn.commit()

            return {"success": True, "message": "Пользователь удалён"}
        except Exception as e:
            logger.error(f"Ошибка полного удаления пользователя: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Методы для работы с приглашениями ====================

    def create_invite_code(
        self,
        code: str,
        created_by: int,
        expires_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создание кода приглашения"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO invite_codes (code, created_by, expires_at, enabled)
                VALUES (?, ?, ?, 1)
            ''', (code, created_by, expires_at))
            self.conn.commit()

            return {"success": True, "code": code, "expires_at": expires_at}
        except Exception as e:
            logger.error(f"Ошибка создания кода приглашения: {e}")
            return {"success": False, "error": str(e)}

    def get_invite_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Получение информации о коде приглашения"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ic.*, u.first_name, u.last_name, u.username
            FROM invite_codes ic
            LEFT JOIN users u ON ic.used_by = u.telegram_id
            WHERE ic.code = ?
        ''', (code,))

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def use_invite_code(self, code: str, telegram_id: int) -> bool:
        """Использование кода приглашения"""
        if not self.conn:
            return False

        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                UPDATE invite_codes
                SET used_by = ?, used_at = CURRENT_TIMESTAMP, enabled = 0
                WHERE code = ? AND used_by IS NULL AND enabled = 1
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ''', (telegram_id, code))
            self.conn.commit()

            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка использования кода: {e}")
            return False

    def get_all_invite_codes(self) -> List[Dict[str, Any]]:
        """Получение всех кодов приглашений"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ic.*,
                   creator.first_name as creator_first_name,
                   creator.last_name as creator_last_name,
                   creator.username as creator_username,
                   used_user.first_name as used_user_first_name,
                   used_user.last_name as used_user_last_name,
                   used_user.username as used_user_username
            FROM invite_codes ic
            LEFT JOIN users creator ON ic.created_by = creator.telegram_id
            LEFT JOIN users used_user ON ic.used_by = used_user.telegram_id
            ORDER BY ic.created_at DESC
        ''')

        return [dict(row) for row in cursor.fetchall()]

    def deactivate_invite_code(self, code: str) -> bool:
        """Деактивация кода приглашения"""
        if not self.conn:
            return False

        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                UPDATE invite_codes SET enabled = 0 WHERE code = ?
            ''', (code,))
            self.conn.commit()

            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка деактивации кода: {e}")
            return False

    def update_user_admin_status(self, telegram_id: int, is_admin: bool) -> bool:
        """Обновление статуса администратора пользователя"""
        if not self.conn:
            return False

        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                UPDATE users SET is_admin = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (1 if is_admin else 0, telegram_id))
            self.conn.commit()

            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка обновления статуса администратора: {e}")
            return False

    def toggle_user_active_status(self, telegram_id: int, is_active: bool) -> Dict[str, Any]:
        """Переключение статуса активности пользователя"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Если деактивируем — удаляем все записи на тренировки
            if not is_active:
                self.remove_user_from_all_trainings(telegram_id)

            cursor.execute('''
                UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (1 if is_active else 0, telegram_id))
            self.conn.commit()

            return {"success": True, "is_active": is_active}
        except Exception as e:
            logger.error(f"Ошибка переключения статуса: {e}")
            return {"success": False, "error": str(e)}

    def remove_user_from_all_trainings(self, telegram_id: int) -> Dict[str, Any]:
        """Удаление всех записей пользователя на тренировки с переносом waitlist"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        removed_count = 0

        try:
            # Получаем все записи пользователя
            cursor.execute('''
                SELECT training_date, training_time, chat_id, status
                FROM training_registrations
                WHERE user_telegram_id = ?
            ''', (telegram_id,))

            trainings = cursor.fetchall()

            # Для каждой записи удаляем и переносим waitlist
            for training in trainings:
                # Удаляем запись
                cursor.execute('''
                    DELETE FROM training_registrations
                    WHERE training_date = ? AND training_time = ? AND chat_id = ? AND user_telegram_id = ?
                ''', (training['training_date'], training['training_time'], training['chat_id'], telegram_id))

                # Находим первого в waitlist и переводим в registered
                cursor.execute('''
                    SELECT id FROM training_registrations
                    WHERE training_date = ? AND training_time = ? AND chat_id = ? AND status = 'waitlist'
                    ORDER BY registered_at ASC
                    LIMIT 1
                ''', (training['training_date'], training['training_time'], training['chat_id']))

                waitlist_user = cursor.fetchone()
                if waitlist_user:
                    cursor.execute('''
                        UPDATE training_registrations
                        SET status = 'registered'
                        WHERE id = ?
                    ''', (waitlist_user['id'],))

                removed_count += 1

            self.conn.commit()

            return {"success": True, "removed_count": removed_count}
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя из тренировок: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Методы для статистики ====================

    def get_users_count(self) -> int:
        """Получение общего количества пользователей"""
        if not self.conn:
            return 0

        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        return cursor.fetchone()[0]

    def get_registrations_count(self, days: int = 30) -> int:
        """Получение количества записей (тренировки + игры) за период"""
        if not self.conn:
            return 0

        cursor = self.conn.cursor()
        
        # Считаем записи на тренировки
        cursor.execute('''
            SELECT COUNT(*) FROM training_registrations
            WHERE registered_at >= datetime('now', '-' || ? || ' days')
        ''', (days,))
        training_count = cursor.fetchone()[0]
        
        # Считаем записи на игры
        cursor.execute('''
            SELECT COUNT(*) FROM game_signups gs
            INNER JOIN games g ON gs.game_id = g.id
            WHERE gs.created_at >= datetime('now', '-' || ? || ' days')
        ''', (days,))
        game_count = cursor.fetchone()[0]
        
        return training_count + game_count

    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних активностей (записи на тренировки и игры из event_signups)"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Получаем последние записи из event_signups (новая архитектура)
        cursor.execute('''
            SELECT
                e.date as activity_date,
                e.start_time as activity_time,
                e.chat_id,
                es.status,
                es.created_at as registered_at,
                u.telegram_id,
                u.first_name,
                u.last_name,
                u.username,
                CASE 
                    WHEN e.event_type = 'game' THEN 'game'
                    ELSE 'training'
                END as activity_type,
                e.name as event_name
            FROM event_signups es
            INNER JOIN events e ON es.event_id = e.id
            INNER JOIN users u ON es.user_id = u.id
            WHERE u.is_active = 1
            ORDER BY es.created_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        
        # Если записей мало, дополняем из старых таблиц (для обратной совместимости)
        if len(rows) < limit:
            # Дополняем из training_registrations
            cursor.execute('''
                SELECT
                    tr.training_date as activity_date,
                    tr.training_time as activity_time,
                    tr.chat_id,
                    tr.status,
                    tr.registered_at,
                    u.telegram_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    'training' as activity_type,
                    COALESCE(ot.name, ps.name, 'Тренировка') as event_name
                FROM training_registrations tr
                LEFT JOIN users u ON tr.user_telegram_id = u.telegram_id
                LEFT JOIN one_time_trainings ot
                    ON tr.training_date = ot.training_date
                    AND tr.training_time = ot.training_time
                    AND tr.chat_id = ot.chat_id
                LEFT JOIN poll_schedules ps
                    ON tr.chat_id = ps.chat_id
                    AND tr.training_time = (ps.start_time || ' - ' || ps.end_time)
                WHERE u.is_active = 1
                  AND tr.registered_at > (SELECT COALESCE(MAX(created_at), 0) FROM event_signups)
                ORDER BY tr.registered_at DESC
                LIMIT ?
            ''', (limit - len(rows),))

            rows.extend([dict(row) for row in cursor.fetchall()])

        return [dict(row) for row in rows]

    # ==================== Методы для работы с events (новая архитектура) ====================

    def get_events(self, year: Optional[int] = None, month: Optional[int] = None,
                   event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получение всех событий за месяц"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        query = 'SELECT * FROM events WHERE 1=1'
        params = []

        if year and month:
            query += ' AND strftime("%Y", date) = ? AND strftime("%m", date) = ?'
            # Преобразуем в int и затем в строку с ведущим нулём
            params.extend([str(int(year)), str(int(month)).zfill(2)])

        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)

        query += ' ORDER BY date ASC, start_time ASC'

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_event_by_uuid(self, event_uuid: str) -> Optional[Dict[str, Any]]:
        """Получение события по UUID"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM events WHERE uuid = ?', (event_uuid,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получение события по ID"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_event_participants(self, event_id: int) -> List[Dict[str, Any]]:
        """Получение всех участников события"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT es.*, u.telegram_id, u.first_name, u.last_name, u.username, u.photo_url, 
                   u.is_admin, u.is_guest
            FROM event_signups es
            JOIN users u ON es.user_id = u.id
            WHERE es.event_id = ? AND u.is_active = 1
            ORDER BY es.created_at ASC
        ''', (event_id,))
        
        participants = []
        for row in cursor.fetchall():
            participant = dict(row)
            participant['is_admin'] = bool(participant.get('is_admin', 0))
            participant['is_guest'] = bool(participant.get('is_guest', 0))
            participants.append(participant)
        
        return participants

    def add_event_signup(self, event_id: int, user_id: int, is_guest: bool = False) -> Dict[str, Any]:
        """Запись пользователя на событие"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Проверяем, есть ли уже запись
            cursor.execute('''
                SELECT id, status FROM event_signups
                WHERE event_id = ? AND user_id = ?
            ''', (event_id, user_id))

            existing = cursor.fetchone()
            if existing:
                return {"success": True, "status": existing['status'], "message": "Уже записан"}

            # Получаем событие для проверки лимита
            cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
            event = cursor.fetchone()
            if not event:
                return {"success": False, "error": "Событие не найдено"}

            # Считаем количество записанных (не включая waitlist)
            cursor.execute('''
                SELECT COUNT(*) as count FROM event_signups
                WHERE event_id = ? AND status = 'registered'
            ''', (event_id,))

            result = cursor.fetchone()
            registered_count = result['count'] if result else 0

            # Определяем статус (лимит 12 человек)
            status = 'registered' if registered_count < 12 else 'waitlist'

            # Создаём запись
            cursor.execute('''
                INSERT INTO event_signups (event_id, user_id, status, is_guest, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (event_id, user_id, status, 1 if is_guest else 0))

            self.conn.commit()

            return {"success": True, "status": status, "message": "Запись успешна"}

        except Exception as e:
            logger.error(f"Ошибка записи на событие: {e}")
            return {"success": False, "error": str(e)}

    def add_event_signup_to_training(self, event_id: int, user_telegram_id: int) -> Dict[str, Any]:
        """Запись пользователя на тренировку по event_id и telegram_id"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Получаем user_id по telegram_id
            cursor.execute('SELECT id, is_guest FROM users WHERE telegram_id = ?', (user_telegram_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return {"success": False, "error": "Пользователь не найден"}

            user_dict = dict(user_row)
            user_id = user_dict['id']
            is_guest = bool(user_dict.get('is_guest', 0))

            # Проверяем, есть ли уже запись
            cursor.execute('''
                SELECT id, status FROM event_signups
                WHERE event_id = ? AND user_id = ?
            ''', (event_id, user_id))

            existing = cursor.fetchone()
            if existing:
                return {"success": True, "status": existing['status'], "message": "Уже записан"}

            # Получаем событие для проверки лимита
            cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
            event = cursor.fetchone()
            if not event:
                return {"success": False, "error": "Событие не найдено"}

            # Считаем количество записанных (не включая waitlist)
            cursor.execute('''
                SELECT COUNT(*) as count FROM event_signups
                WHERE event_id = ? AND status = 'registered'
            ''', (event_id,))

            result = cursor.fetchone()
            registered_count = result['count'] if result else 0

            # Определяем статус (лимит 12 человек)
            status = 'registered' if registered_count < 12 else 'waitlist'

            # Создаём запись
            cursor.execute('''
                INSERT INTO event_signups (event_id, user_id, status, is_guest, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (event_id, user_id, status, 1 if is_guest else 0))

            self.conn.commit()

            return {"success": True, "status": status}

        except Exception as e:
            logger.error(f"Ошибка записи на тренировку: {e}")
            return {"success": False, "error": str(e)}

    def remove_event_signup(self, event_id: int, user_id: int) -> Dict[str, Any]:
        """Отмена записи на событие + удаление из старых таблиц"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Получаем информацию о событии
            cursor.execute('SELECT event_type, source_table, source_id, date, start_time, chat_id FROM events WHERE id = ?', (event_id,))
            event = cursor.fetchone()

            if not event:
                return {"success": False, "error": "Событие не найдено"}

            # Получаем telegram_id пользователя
            cursor.execute('SELECT telegram_id FROM users WHERE id = ?', (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return {"success": False, "error": "Пользователь не найден"}

            telegram_id = dict(user_row)['telegram_id']
            event_dict = dict(event)

            # Удаляем из event_signups
            cursor.execute('''
                DELETE FROM event_signups
                WHERE event_id = ? AND user_id = ?
            ''', (event_id, user_id))

            # Удаляем из старых таблиц в зависимости от типа события
            if event_dict['event_type'] in ('training', 'scheduled_training', 'one_time_training'):
                # Удаляем из training_registrations
                cursor.execute('''
                    DELETE FROM training_registrations
                    WHERE user_telegram_id = ? AND training_date = ? AND training_time = ? AND chat_id = ?
                ''', (telegram_id, event_dict['date'], event_dict['start_time'], event_dict['chat_id']))

                # Удаляем из guest_signups
                cursor.execute('''
                    DELETE FROM guest_signups
                    WHERE user_telegram_id = ? AND training_uuid = (SELECT uuid FROM events WHERE id = ?)
                ''', (telegram_id, event_id))

            elif event_dict['event_type'] == 'game':
                # Удаляем из game_signups
                cursor.execute('''
                    DELETE FROM game_signups
                    WHERE user_telegram_id = ? AND game_id = ?
                ''', (telegram_id, event_dict['source_id']))

            # Также удаляем напрямую из guest_signups по training_uuid если есть
            if event_dict['source_table'] in ('scheduled_trainings', 'one_time_trainings'):
                cursor.execute('''
                    DELETE FROM guest_signups
                    WHERE user_telegram_id = ? AND training_uuid = (SELECT uuid FROM events WHERE id = ?)
                ''', (telegram_id, event_id))

            self.conn.commit()

            if cursor.rowcount > 0:
                return {"success": True, "message": "Запись отменена"}
            else:
                return {"success": False, "error": "Запись не найдена"}

        except Exception as e:
            logger.error(f"Ошибка отмены записи: {e}")
            return {"success": False, "error": str(e)}

    def remove_event_signup_by_telegram(self, event_id: int, user_telegram_id: int) -> Dict[str, Any]:
        """Отмена записи на событие по telegram_id"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Получаем информацию о событии
            cursor.execute('SELECT event_type, source_table, source_id, date, start_time, chat_id FROM events WHERE id = ?', (event_id,))
            event = cursor.fetchone()

            if not event:
                return {"success": False, "error": "Событие не найдено"}

            # Получаем user_id по telegram_id
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_telegram_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return {"success": False, "error": "Пользователь не найден"}

            user_id = dict(user_row)['id']
            event_dict = dict(event)

            # Проверяем существование записи перед удалением
            cursor.execute('''
                SELECT id FROM event_signups
                WHERE event_id = ? AND user_id = ?
            ''', (event_id, user_id))

            existing_signup = cursor.fetchone()
            if not existing_signup:
                # Записи нет, но это не ошибка — просто возвращаем успех
                return {"success": True, "message": "Запись не найдена"}

            # Удаляем из event_signups
            cursor.execute('''
                DELETE FROM event_signups
                WHERE event_id = ? AND user_id = ?
            ''', (event_id, user_id))

            # Удаляем из старых таблиц в зависимости от типа события
            if event_dict['event_type'] in ('training', 'scheduled_training', 'one_time_training'):
                # Удаляем из training_registrations
                cursor.execute('''
                    DELETE FROM training_registrations
                    WHERE user_telegram_id = ? AND training_date = ? AND training_time = ? AND chat_id = ?
                ''', (user_telegram_id, event_dict['date'], event_dict['start_time'], event_dict['chat_id']))

                # Удаляем из guest_signups
                cursor.execute('''
                    DELETE FROM guest_signups
                    WHERE user_telegram_id = ? AND training_uuid = (SELECT uuid FROM events WHERE id = ?)
                ''', (user_telegram_id, event_id))

            elif event_dict['event_type'] == 'game':
                # Удаляем из game_signups
                cursor.execute('''
                    DELETE FROM game_signups
                    WHERE user_telegram_id = ? AND game_id = ?
                ''', (user_telegram_id, event_dict['source_id']))

            # Также удаляем напрямую из guest_signups по training_uuid если есть
            if event_dict['source_table'] in ('scheduled_trainings', 'one_time_trainings'):
                cursor.execute('''
                    DELETE FROM guest_signups
                    WHERE user_telegram_id = ? AND training_uuid = (SELECT uuid FROM events WHERE id = ?)
                ''', (user_telegram_id, event_id))

            self.conn.commit()

            return {"success": True, "message": "Запись отменена"}

        except Exception as e:
            logger.error(f"Ошибка отмены записи: {e}")
            return {"success": False, "error": str(e)}

    def remove_event(self, event_id: int) -> Dict[str, Any]:
        """Удаление события (только для администратора)"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Получаем информацию о событии
            cursor.execute('SELECT event_type, uuid FROM events WHERE id = ?', (event_id,))
            event = cursor.fetchone()

            if not event:
                # Событие не найдено в таблице events - пробуем удалить как старую тренировку
                # Ищем в one_time_trainings по UUID
                cursor.execute('''
                    SELECT id FROM one_time_trainings WHERE uuid = ?
                ''', (str(event_id),))
                ottp = cursor.fetchone()
                if ottp:
                    return self.remove_one_time_training(ottp['id'])
                
                # Ищем в scheduled_trainings по UUID
                cursor.execute('''
                    SELECT id FROM scheduled_trainings WHERE uuid = ?
                ''', (str(event_id),))
                st = cursor.fetchone()
                if st:
                    return self.remove_scheduled_training(st['id'])
                
                return {"success": False, "error": "Тренировка не найдена"}

            event_dict = dict(event)

            # Удаляем все записи на это событие
            cursor.execute('DELETE FROM event_signups WHERE event_id = ?', (event_id,))

            # Удаляем из старых таблиц в зависимости от типа события
            if event_dict['event_type'] in ('training', 'scheduled_training', 'one_time_training'):
                # Удаляем из training_registrations
                cursor.execute('''
                    DELETE FROM training_registrations
                    WHERE training_date = (SELECT date FROM events WHERE id = ?)
                    AND training_time = (SELECT start_time FROM events WHERE id = ?)
                    AND chat_id = (SELECT chat_id FROM events WHERE id = ?)
                ''', (event_id, event_id, event_id))

                # Удаляем из guest_signups по training_uuid
                cursor.execute('''
                    DELETE FROM guest_signups
                    WHERE training_uuid = ?
                ''', (event_dict['uuid'],))

            elif event_dict['event_type'] == 'game':
                # Удаляем из game_signups
                cursor.execute('''
                    DELETE FROM game_signups
                    WHERE game_id = ?
                ''', (event_dict['uuid'],))

            # Удаляем само событие
            cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))

            self.conn.commit()

            return {"success": True, "message": "Событие удалено"}

        except Exception as e:
            logger.error(f"Ошибка удаления события: {e}")
            return {"success": False, "error": str(e)}

    def remove_event_by_uuid(self, event_uuid: str) -> Dict[str, Any]:
        """Удаление события по UUID (только для администратора)"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Получаем информацию о событии по UUID
            cursor.execute('SELECT id, event_type, uuid, source_table, source_id FROM events WHERE uuid = ?', (event_uuid,))
            event = cursor.fetchone()

            if not event:
                return {"success": False, "error": "Событие не найдено"}

            event_dict = dict(event)
            event_id = event_dict['id']

            # Удаляем все записи на это событие
            cursor.execute('DELETE FROM event_signups WHERE event_id = ?', (event_id,))

            # Удаляем из старых таблиц в зависимости от типа события
            if event_dict['event_type'] in ('training', 'scheduled_training', 'one_time_training'):
                # Удаляем из training_registrations
                cursor.execute('''
                    DELETE FROM training_registrations
                    WHERE training_date = (SELECT date FROM events WHERE id = ?)
                    AND training_time = (SELECT start_time FROM events WHERE id = ?)
                    AND chat_id = (SELECT chat_id FROM events WHERE id = ?)
                ''', (event_id, event_id, event_id))

                # Удаляем из guest_signups по training_uuid
                cursor.execute('''
                    DELETE FROM guest_signups
                    WHERE training_uuid = ?
                ''', (event_uuid,))

            elif event_dict['event_type'] == 'game':
                # Удаляем из game_signups
                cursor.execute('''
                    DELETE FROM game_signups
                    WHERE game_id = ?
                ''', (event_dict['source_id'],))

            # Удаляем из исходной таблицы
            if event_dict['source_table'] == 'one_time_trainings':
                cursor.execute('DELETE FROM one_time_trainings WHERE uuid = ?', (event_uuid,))
            elif event_dict['source_table'] == 'scheduled_trainings':
                cursor.execute('DELETE FROM scheduled_trainings WHERE uuid = ?', (event_uuid,))
            elif event_dict['source_table'] == 'games':
                cursor.execute('DELETE FROM games WHERE uuid = ?', (event_uuid,))

            # Удаляем само событие
            cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))

            self.conn.commit()

            return {"success": True, "message": "Событие удалено"}

        except Exception as e:
            logger.error(f"Ошибка удаления события: {e}")
            return {"success": False, "error": str(e)}

    def get_user_events(self, user_id: int, year: Optional[int] = None, 
                        month: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение всех событий, на которые записан пользователь"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        query = '''
            SELECT e.*, es.status, es.is_guest as signup_as_guest
            FROM events e
            JOIN event_signups es ON e.id = es.event_id
            WHERE es.user_id = ?
        '''
        params = [user_id]
        
        if year and month:
            query += ' AND strftime("%Y", e.date) = ? AND strftime("%m", e.date) = ?'
            params.extend([str(year), str(month).zfill(2)])
        
        query += ' ORDER BY e.date ASC, e.start_time ASC'
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ==================== Методы для работы с играми ====================

    def get_all_games(self, year: Optional[int] = None, month: Optional[int] = None) -> List[Dict[str, Any]]:
        """Получение всех игр"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        if year and month:
            cursor.execute('''
                SELECT * FROM games
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
                ORDER BY date ASC, start_time ASC
            ''', (str(year), str(month).zfill(2)))
        else:
            cursor.execute('SELECT * FROM games ORDER BY date ASC, start_time ASC')

        return [dict(row) for row in cursor.fetchall()]

    def get_game(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Получение игры по ID (из games или events)"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        
        # Сначала пробуем найти в events (новая архитектура)
        cursor.execute("SELECT * FROM events WHERE id = ? AND event_type = 'game'", (game_id,))
        event_row = cursor.fetchone()
        if event_row:
            event = dict(event_row)
            # Нормализуем поля для обратной совместимости
            return {
                'id': event['id'],
                'uuid': event.get('uuid'),
                'name': event.get('name', ''),
                'date': event.get('date'),
                'location': event.get('location', ''),
                'start_time': event.get('start_time'),
                'end_time': event.get('end_time'),
                'opponent': event.get('opponent'),
                'result': event.get('result'),
                'score': event.get('score'),
                'chat_id': event.get('chat_id'),
                'topic_id': event.get('topic_id'),
                'from_events': True
            }
        
        # Если не найдено, пробуем в games (старая архитектура)
        cursor.execute('SELECT * FROM games WHERE id = ?', (game_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_training_by_uuid(self, training_uuid: str) -> Optional[Dict[str, Any]]:
        """Получение тренировки по UUID (из games, scheduled_trainings или one_time_trainings)"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        
        # Пробуем найти в games
        cursor.execute('SELECT * FROM games WHERE uuid = ?', (training_uuid,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['source'] = 'games'
            return result
        
        # Пробуем найти в scheduled_trainings
        cursor.execute('SELECT * FROM scheduled_trainings WHERE uuid = ?', (training_uuid,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['source'] = 'scheduled_trainings'
            return result
        
        # Пробуем найти в one_time_trainings
        cursor.execute('SELECT * FROM one_time_trainings WHERE uuid = ?', (training_uuid,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result['source'] = 'one_time_trainings'
            return result
        
        return None

    def get_training_id_by_uuid(self, training_uuid: str) -> Optional[str]:
        """
        Получение ID тренировки по UUID (из games, scheduled_trainings или one_time_trainings)

        Args:
            training_uuid: UUID тренировки

        Returns:
            ID тренировки или None если не найдена
        """
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        
        # Пробуем найти в games
        cursor.execute('SELECT id FROM games WHERE uuid = ?', (training_uuid,))
        row = cursor.fetchone()
        if row:
            return row['id']
        
        # Пробуем найти в scheduled_trainings
        cursor.execute('SELECT id FROM scheduled_trainings WHERE uuid = ?', (training_uuid,))
        row = cursor.fetchone()
        if row:
            return row['id']
        
        # Пробуем найти в one_time_trainings
        cursor.execute('SELECT id FROM one_time_trainings WHERE uuid = ?', (training_uuid,))
        row = cursor.fetchone()
        if row:
            return row['id']
        
        return None

    def get_training_uuid_by_id(self, training_id: str) -> Optional[str]:
        """Получение UUID тренировки по ID"""
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('SELECT uuid FROM games WHERE id = ?', (training_id,))
        row = cursor.fetchone()
        if row:
            return row['uuid']
        return None

    def add_game(self, game: Dict[str, Any]) -> Dict[str, Any]:
        """Добавление игры"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        game_id = game.get('id', str(datetime.now().timestamp()))
        # Генерируем UUID если не предоставлен
        game_uuid = game.get('uuid', str(uuid_module.uuid4()))

        try:
            cursor.execute('''
                INSERT INTO games (id, uuid, name, date, location, start_time, opponent, chat_id, topic_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_id,
                game_uuid,
                game['name'],
                game['date'],
                game.get('location', ''),
                game.get('start_time'),
                game.get('opponent', ''),
                game.get('chat_id', ''),
                game.get('topic_id')
            ))
            self.conn.commit()
            return {"success": True, "id": game_id, "uuid": game_uuid}
        except Exception as e:
            logger.error(f"Ошибка добавления игры: {e}")
            return {"success": False, "error": str(e)}

    def update_game(self, game_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление игры"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        
        # Добавляем updated_at
        updates['updated_at'] = 'CURRENT_TIMESTAMP'
        
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [game_id]

        try:
            cursor.execute(f'''
                UPDATE games
                SET {set_clause}
                WHERE id = ?
            ''', values)
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка обновления игры: {e}")
            return {"success": False, "error": str(e)}

    def remove_game(self, game_id: str) -> Dict[str, Any]:
        """Удаление игры"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            # Удаляем все записи на эту игру
            cursor.execute('DELETE FROM game_signups WHERE game_id = ?', (game_id,))
            # Удаляем саму игру
            cursor.execute('DELETE FROM games WHERE id = ?', (game_id,))
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка удаления игры: {e}")
            return {"success": False, "error": str(e)}

    def get_game_signups(self, game_id: str) -> List[Dict[str, Any]]:
        """Получение всех записей на игру (из event_signups + game_signups)"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        # Сначала пробуем найти event для этой игры
        cursor.execute("SELECT id FROM events WHERE source_table = 'games' AND source_id = ?", (game_id,))
        event_row = cursor.fetchone()
        
        if event_row:
            # Получаем из event_signups (новая архитектура)
            event_id = event_row['id']
            cursor.execute('''
                SELECT 
                    es.user_id,
                    u.telegram_id as user_telegram_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    u.photo_url,
                    u.is_admin,
                    es.status,
                    es.created_at,
                    es.is_guest
                FROM event_signups es
                INNER JOIN users u ON es.user_id = u.id
                WHERE es.event_id = ? AND u.is_active = 1
                ORDER BY es.created_at ASC
            ''', (event_id,))
            
            rows = [dict(row) for row in cursor.fetchall()]
        else:
            rows = []
        
        # Дополняем из game_signups (старая архитектура)
        cursor.execute('''
            SELECT gs.*, u.first_name, u.last_name, u.username, u.photo_url, u.is_admin, 0 as is_guest
            FROM game_signups gs
            LEFT JOIN users u ON gs.user_telegram_id = u.telegram_id
            WHERE gs.game_id = ? AND u.is_active = 1
            ORDER BY gs.created_at ASC
        ''', (game_id,))

        rows.extend([dict(row) for row in cursor.fetchall()])

        # Дедупликация по user_telegram_id (если пользователь есть в обеих таблицах)
        seen = set()
        unique_rows = []
        for row in rows:
            telegram_id = row.get('user_telegram_id')
            if telegram_id not in seen:
                seen.add(telegram_id)
                unique_rows.append(row)

        # Преобразуем поля в bool
        for row in unique_rows:
            if 'is_admin' in row:
                row['is_admin'] = bool(row['is_admin'])
            if 'is_guest' in row:
                row['is_guest'] = bool(row['is_guest'])

        return unique_rows

    def get_training_participants(self, training_uuid: str) -> List[Dict[str, Any]]:
        """
        Получение всех участников тренировки по UUID

        Возвращает как пользователей, так и гостей с флагом is_guest

        Args:
            training_uuid: UUID тренировки

        Returns:
            Список участников с флагом is_guest
        """
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Сначала находим event по uuid
        cursor.execute("SELECT id FROM events WHERE uuid = ?", (training_uuid,))
        event_row = cursor.fetchone()

        if event_row:
            event_id = dict(event_row)['id']

            # Получаем участников из event_signups (новая архитектура)
            cursor.execute('''
                SELECT
                    u.telegram_id as user_telegram_id,
                    es.created_at as registered_at,
                    u.first_name,
                    u.last_name,
                    u.username,
                    u.photo_url,
                    CASE WHEN u.is_guest = 1 THEN 1 ELSE 0 END as is_guest,
                    u.is_admin,
                    u.is_guest,
                    es.status
                FROM event_signups es
                JOIN users u ON es.user_id = u.id
                WHERE es.event_id = ? AND u.is_active = 1
                ORDER BY es.created_at ASC
            ''', (event_id,))

            participants = [dict(row) for row in cursor.fetchall()]
            
            # Если в event_signups пусто, пробуем получить из training_registrations (старая архитектура)
            if not participants:
                participants = self.get_training_registrations_by_uuid(training_uuid)
        else:
            # Event не найден, пробуем получить из training_registrations (старая архитектура)
            participants = self.get_training_registrations_by_uuid(training_uuid)

        return participants

    def signup_for_game(self, game_id: str, user_telegram_id: int) -> Dict[str, Any]:
        """Запись на игру (из events или games)"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        # Проверяем, является ли game_id event_id
        cursor.execute("SELECT id, event_type FROM events WHERE id = ?", (game_id,))
        event_row = cursor.fetchone()

        if event_row:
            # Это event из новой таблицы
            event_id = dict(event_row)['id']
            
            # Получаем user_id
            cursor.execute('SELECT id, is_guest FROM users WHERE telegram_id = ?', (user_telegram_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return {"success": False, "error": "Пользователь не найден"}
            
            user_id = dict(user_row)['id']
            is_guest = bool(dict(user_row).get('is_guest', 0))
            
            # Проверяем существующую запись
            cursor.execute('''
                SELECT id, status FROM event_signups
                WHERE event_id = ? AND user_id = ?
            ''', (event_id, user_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Если уже записан - отменяем запись (удаляем)
                cursor.execute('''
                    DELETE FROM event_signups
                    WHERE event_id = ? AND user_id = ?
                ''', (event_id, user_id))
                self.conn.commit()
                return {"success": True, "action": "removed"}
            else:
                # Создаём новую запись
                cursor.execute('''
                    INSERT INTO event_signups (event_id, user_id, status, is_guest, created_at)
                    VALUES (?, ?, 'registered', ?, CURRENT_TIMESTAMP)
                ''', (event_id, user_id, 1 if is_guest else 0))
                self.conn.commit()
                return {"success": True, "action": "registered", "status": "registered"}
        else:
            # Старая архитектура: game_signups + дублирование в event_signups
            signup_id = f"{game_id}_{user_telegram_id}_{datetime.now().timestamp()}"

            try:
                # Проверяем, есть ли уже запись
                cursor.execute('''
                    SELECT id, status FROM game_signups
                    WHERE game_id = ? AND user_telegram_id = ?
                ''', (game_id, user_telegram_id))

                existing = cursor.fetchone()

                if existing:
                    # Если уже записан - отменяем запись (удаляем)
                    cursor.execute('''
                        DELETE FROM game_signups
                        WHERE game_id = ? AND user_telegram_id = ?
                    ''', (game_id, user_telegram_id))

                    # Также удаляем из event_signups
                    cursor.execute('''
                        SELECT id FROM events WHERE source_table = 'games' AND source_id = ?
                    ''', (game_id,))
                    event_row2 = cursor.fetchone()
                    if event_row2:
                        event_id = dict(event_row2)['id']
                        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_telegram_id,))
                        user_row2 = cursor.fetchone()
                        if user_row2:
                            user_id = dict(user_row2)['id']
                            cursor.execute('''
                                DELETE FROM event_signups
                                WHERE event_id = ? AND user_id = ?
                            ''', (event_id, user_id))

                    self.conn.commit()
                    return {"success": True, "action": "removed"}
                else:
                    # Создаём новую запись
                    cursor.execute('''
                        INSERT INTO game_signups (id, game_id, user_telegram_id, status, created_at, updated_at)
                        VALUES (?, ?, ?, 'registered', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (signup_id, game_id, user_telegram_id))

                    # Дублируем в event_signups
                    cursor.execute('''
                        SELECT id FROM events WHERE source_table = 'games' AND source_id = ?
                    ''', (game_id,))
                    event_row3 = cursor.fetchone()
                    if event_row3:
                        event_id = dict(event_row3)['id']
                        cursor.execute('SELECT id, is_guest FROM users WHERE telegram_id = ?', (user_telegram_id,))
                        user_row3 = cursor.fetchone()
                        if user_row3:
                            user_id = dict(user_row3)['id']
                            is_guest = bool(dict(user_row3).get('is_guest', 0))

                            # Проверяем существующую запись
                            cursor.execute('''
                                SELECT id FROM event_signups
                                WHERE event_id = ? AND user_id = ?
                            ''', (event_id, user_id))

                            if not cursor.fetchone():
                                cursor.execute('''
                                    INSERT INTO event_signups (event_id, user_id, status, is_guest, created_at)
                                    VALUES (?, ?, 'registered', ?, CURRENT_TIMESTAMP)
                                ''', (event_id, user_id, 1 if is_guest else 0))

                    self.conn.commit()
                    return {"success": True, "action": "registered", "status": "registered"}
            except Exception as e:
                logger.error(f"Ошибка записи на игру: {e}")
                return {"success": False, "error": str(e)}

    def unregister_from_game(self, game_id: str, user_telegram_id: int) -> Dict[str, Any]:
        """Отписка от игры"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                DELETE FROM game_signups
                WHERE game_id = ? AND user_telegram_id = ?
            ''', (game_id, user_telegram_id))
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка отписки от игры: {e}")
            return {"success": False, "error": str(e)}

    def set_game_result(self, game_id: str, result: str, score: str) -> Dict[str, Any]:
        """Установка результата игры"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                UPDATE games
                SET result = ?, score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (result, score, game_id))
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка установки результата игры: {e}")
            return {"success": False, "error": str(e)}

    def get_user_games(self, user_telegram_id: int) -> List[Dict[str, Any]]:
        """Получение всех игр, на которые записан пользователь (из event_signups + game_signups)"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        # Сначала получаем из event_signups (новая архитектура)
        cursor.execute('''
            SELECT 
                e.*,
                es.status as signup_status,
                es.created_at as registered_at,
                es.is_guest
            FROM event_signups es
            INNER JOIN events e ON es.event_id = e.id
            INNER JOIN users u ON es.user_id = u.id
            WHERE u.telegram_id = ? AND e.event_type = 'game'
            ORDER BY e.date ASC, e.start_time ASC
        ''', (user_telegram_id,))
        
        rows = cursor.fetchall()
        
        # Дополняем из game_signups (старая архитектура)
        cursor.execute('''
            SELECT g.*, gs.status as signup_status, gs.created_at as registered_at, 0 as is_guest
            FROM games g
            INNER JOIN game_signups gs ON g.id = gs.game_id
            WHERE gs.user_telegram_id = ?
              AND gs.created_at > (SELECT COALESCE(MAX(created_at), 0) FROM event_signups)
            ORDER BY g.date ASC, g.start_time ASC
        ''', (user_telegram_id,))
        
        rows.extend([dict(row) for row in cursor.fetchall()])
        
        return [dict(row) for row in rows]

    # ==================== Методы для работы с гостями ====================

    def add_guest(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Добавление гостя (создание записи в таблице users с is_guest=1)

        Args:
            telegram_id: Telegram ID пользователя
            first_name: Имя пользователя
            last_name: Фамилия (опционально)
            username: Username (опционально)
            photo_url: URL фото профиля (опционально)

        Returns:
            Dict с информацией о госте или None если ошибка
        """
        if not self.conn:
            logger.error("Нельзя добавить гостя: база данных не подключена")
            return None

        cursor = self.conn.cursor()
        try:
            # Проверяем существует ли уже пользователь с таким telegram_id
            cursor.execute('''
                SELECT * FROM users WHERE telegram_id = ?
            ''', (telegram_id,))
            existing = cursor.fetchone()

            if existing:
                # Обновляем существующего пользователя как гостя
                cursor.execute('''
                    UPDATE users 
                    SET is_guest = 1,
                        first_name = ?,
                        last_name = COALESCE(?, last_name),
                        username = COALESCE(?, username),
                        photo_url = COALESCE(?, photo_url),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (first_name, last_name, username, photo_url, telegram_id))
                self.conn.commit()
                logger.info(f"Гость обновлён: {telegram_id}")
                return self.get_guest_by_telegram(telegram_id)

            # Создаём нового пользователя-гостя
            cursor.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, username, photo_url, is_guest, is_admin, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (telegram_id, first_name, last_name, username, photo_url))
            self.conn.commit()
            logger.info(f"Гость добавлен: {telegram_id}")
            return self.get_guest_by_telegram(telegram_id)
        except sqlite3.IntegrityError as e:
            logger.error(f"Ошибка добавления гостя (нарушение целостности): {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка добавления гостя: {e}")
            return None

    def add_guest_signup(
        self,
        telegram_id: int,
        training_uuid: str,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Запись гостя на тренировку
        
        Создаёт гостя если не существует, и добавляет запись в guest_signups

        Args:
            telegram_id: Telegram ID пользователя
            training_uuid: UUID тренировки
            first_name: Имя пользователя
            last_name: Фамилия (опционально)
            username: Username (опционально)
            photo_url: URL фото профиля (опционально)

        Returns:
            Dict с информацией о записи или None если ошибка
        """
        if not self.conn:
            logger.error("Нельзя записать гостя: база данных не подключена")
            return None

        cursor = self.conn.cursor()
        try:
            # Создаём гостя если не существует
            guest = self.add_guest(telegram_id, first_name, last_name, username, photo_url)
            if not guest:
                return None

            # Получаем ID пользователя
            user = self.get_user_by_telegram_id(telegram_id)
            if not user:
                logger.error(f"Пользователь {telegram_id} не найден после создания")
                return None
            
            user_id = user['id']

            # Проверяем, существует ли уже запись
            cursor.execute('''
                SELECT * FROM guest_signups
                WHERE user_telegram_id = ? AND training_uuid = ?
            ''', (user_id, training_uuid))
            existing = cursor.fetchone()

            if existing:
                logger.info(f"Гость {telegram_id} уже записан на тренировку {training_uuid}")
                return dict(existing)

            # Добавляем запись в guest_signups
            signup_id = f"signup_{user_id}_{training_uuid}"
            cursor.execute('''
                INSERT INTO guest_signups (id, user_telegram_id, training_uuid, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (signup_id, user_id, training_uuid))
            self.conn.commit()
            logger.info(f"Гость {telegram_id} записан на тренировку {training_uuid}")
            return self.get_guest_signup(telegram_id, training_uuid)
        except sqlite3.IntegrityError as e:
            logger.error(f"Ошибка записи гостя (нарушение целостности): {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка записи гостя: {e}")
            return None

    def get_guest_signup(self, telegram_id: int, training_uuid: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о записи гостя на тренировку

        Args:
            telegram_id: Telegram ID пользователя
            training_uuid: UUID тренировки

        Returns:
            Dict с информацией о записи или None если не найдена
        """
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        
        # Получаем ID пользователя
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return None
        
        user_id = user['id']
        
        cursor.execute('''
            SELECT gs.*, u.first_name, u.last_name, u.username, u.photo_url, u.is_active
            FROM guest_signups gs
            JOIN users u ON gs.user_telegram_id = u.id
            WHERE gs.user_telegram_id = ? AND gs.training_uuid = ?
        ''', (user_id, training_uuid))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_guest_trainings(self, telegram_id: int) -> List[Dict[str, Any]]:
        """
        Получение списка всех тренировок гостя

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Список тренировок гостя
        """
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        
        # Получаем записи из guest_signups и джойним с games, scheduled_trainings, one_time_trainings
        cursor.execute('''
            SELECT gs.user_telegram_id as telegram_id, gs.training_uuid, gs.created_at,
                   gu.uuid as training_uuid, gu.name as training_name, gu.date as training_date,
                   gu.start_time, NULL as end_time, gu.location, 'games' as source
            FROM guest_signups gs
            JOIN games gu ON gs.training_uuid = gu.uuid
            WHERE gs.user_telegram_id = ?

            UNION

            SELECT gs.user_telegram_id as telegram_id, gs.training_uuid, gs.created_at,
                   st.uuid as training_uuid, st.name as training_name, st.training_date as training_date,
                   st.start_time, st.end_time, st.location, 'scheduled_trainings' as source
            FROM guest_signups gs
            JOIN scheduled_trainings st ON gs.training_uuid = st.uuid
            WHERE gs.user_telegram_id = ?

            UNION

            SELECT gs.user_telegram_id as telegram_id, gs.training_uuid, gs.created_at,
                   ot.uuid as training_uuid, ot.name as training_name, ot.training_date as training_date,
                   ot.start_time, ot.end_time, ot.location, 'one_time_trainings' as source
            FROM guest_signups gs
            JOIN one_time_trainings ot ON gs.training_uuid = ot.uuid
            WHERE gs.user_telegram_id = ?

            ORDER BY training_date ASC, start_time ASC
        ''', (telegram_id, telegram_id, telegram_id))

        return [dict(row) for row in cursor.fetchall()]

    def remove_guest_signup(self, telegram_id: int, training_uuid: str) -> Dict[str, Any]:
        """
        Отписка гостя от тренировки

        Args:
            telegram_id: Telegram ID пользователя
            training_uuid: UUID тренировки

        Returns:
            Dict с результатом операции
        """
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        try:
            # Получаем ID пользователя
            user = self.get_user_by_telegram_id(telegram_id)
            if not user:
                return {"success": False, "error": "Пользователь не найден"}
            
            user_id = user['id']
            
            cursor.execute('''
                DELETE FROM guest_signups
                WHERE user_telegram_id = ? AND training_uuid = ?
            ''', (user_id, training_uuid))
            self.conn.commit()

            if cursor.rowcount > 0:
                return {"success": True, "message": "Гость отписан от тренировки"}
            else:
                return {"success": False, "error": "Запись не найдена"}
        except Exception as e:
            logger.error(f"Ошибка отписки гостя: {e}")
            return {"success": False, "error": str(e)}

    def is_guest_signed_up(self, telegram_id: int, training_uuid: str) -> bool:
        """
        Проверка: записан ли гость на тренировку

        Args:
            telegram_id: Telegram ID пользователя
            training_uuid: UUID тренировки

        Returns:
            True если гость записан, False иначе
        """
        if not self.conn:
            return False

        cursor = self.conn.cursor()
        
        # Получаем ID пользователя
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        user_id = user['id']
        
        cursor.execute('''
            SELECT 1 FROM guest_signups
            WHERE user_telegram_id = ? AND training_uuid = ?
        ''', (user_id, training_uuid))
        return cursor.fetchone() is not None

    def get_guest_by_telegram(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о госте по Telegram ID

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict с информацией о госте или None если не найден
        """
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ? AND is_guest = 1', (telegram_id,))
        row = cursor.fetchone()

        if row:
            guest = dict(row)
            guest['is_active'] = bool(guest.get('is_active', 1))
            guest['is_guest'] = True
            return guest
        return None

    def get_guest_with_training(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о госте с данными о тренировке
        (обратная совместимость - возвращает первую тренировку)

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict с информацией о госте и тренировке или None если не найден
        """
        if not self.conn:
            return None

        cursor = self.conn.cursor()
        
        # Получаем ID пользователя
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return None
        
        user_id = user['id']
        
        cursor.execute('''
            SELECT u.*, gu.uuid as training_uuid, gu.name as training_name,
                   gu.date as training_date, gu.start_time, gu.location
            FROM users u
            LEFT JOIN guest_signups gs ON u.id = gs.user_telegram_id
            LEFT JOIN games gu ON gs.training_uuid = gu.uuid
            WHERE u.telegram_id = ? AND u.is_guest = 1
            ORDER BY gu.date ASC
            LIMIT 1
        ''', (telegram_id,))
        row = cursor.fetchone()

        if row:
            guest = dict(row)
            guest['is_active'] = bool(guest.get('is_active', 1))
            guest['is_guest'] = True
            return guest
        return None

    def update_guest_status(self, telegram_id: int, is_active: bool) -> Dict[str, Any]:
        """
        Активация/деактивация гостя

        Args:
            telegram_id: Telegram ID пользователя
            is_active: Статус активности

        Returns:
            Dict с результатом операции
        """
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE guests
                SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (1 if is_active else 0, telegram_id))
            self.conn.commit()

            if cursor.rowcount > 0:
                return {"success": True, "is_active": is_active}
            else:
                return {"success": False, "error": "Гость не найден"}
        except Exception as e:
            logger.error(f"Ошибка обновления статуса гостя: {e}")
            return {"success": False, "error": str(e)}

    def is_guest(self, telegram_id: int) -> bool:
        """
        Проверка: является ли пользователь гостем

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            True если пользователь является гостем, False иначе
        """
        if not self.conn:
            return False

        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE telegram_id = ? AND is_guest = 1', (telegram_id,))
        return cursor.fetchone() is not None

    def get_all_guests(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получение всех гостей с пагинацией

        Args:
            limit: Максимальное количество записей
            offset: Смещение для пагинации

        Returns:
            Список гостей
        """
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT telegram_id, first_name, last_name, username, photo_url, is_active, created_at, updated_at, is_guest
            FROM users
            WHERE is_guest = 1
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        guests = []
        for row in cursor.fetchall():
            guest = dict(row)
            guest['is_active'] = bool(guest.get('is_active', 1))
            guest['is_guest'] = True
            guests.append(guest)

        return guests

    def get_guest_signup_count(self, telegram_id: int) -> int:
        """
        Получение количества тренировок, на которые записан гость

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Количество записей
        """
        if not self.conn:
            return 0

        cursor = self.conn.cursor()
        
        # Получаем ID пользователя
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return 0
        
        user_id = user['id']
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM guest_signups
            WHERE user_telegram_id = ?
        ''', (user_id,))
        row = cursor.fetchone()
        return row['count'] if row else 0

    def convert_guest_to_user(
        self,
        telegram_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Конвертация гостя в пользователя

        Args:
            telegram_id: Telegram ID пользователя
            first_name: Имя (если не предоставлено, берётся из guests)
            last_name: Фамилия
            username: Username
            photo_url: URL фото профиля

        Returns:
            Dict с информацией о новом пользователе или None если ошибка
        """
        if not self.conn:
            logger.error("Нельзя конвертировать гостя: база данных не подключена")
            return None

        cursor = self.conn.cursor()
        try:
            # Получаем данные гостя
            guest = self.get_guest_by_telegram(telegram_id)
            if not guest:
                logger.warning(f"Гость {telegram_id} не найден для конвертации")
                return None

            # Используем данные гостя если не предоставлены
            first_name = first_name or guest['first_name']
            last_name = last_name or guest.get('last_name')
            username = username or guest.get('username')
            photo_url = photo_url or guest.get('photo_url')

            # Проверяем существует ли уже пользователь
            existing_user = self.get_user_by_telegram_id(telegram_id)
            if existing_user:
                logger.warning(f"Пользователь {telegram_id} уже существует")
                # Просто снимаем флаг гостя и удаляем записи
                cursor.execute('DELETE FROM guest_signups WHERE user_telegram_id = (SELECT id FROM users WHERE telegram_id = ?)', (telegram_id,))
                cursor.execute('UPDATE users SET is_guest = 0 WHERE telegram_id = ?', (telegram_id,))
                self.conn.commit()
                return existing_user

            # Создаём пользователя
            cursor.execute('''
                INSERT INTO users (telegram_id, first_name, last_name, username, photo_url, is_admin, is_active, created_at, updated_at, last_login)
                VALUES (?, ?, ?, ?, ?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (telegram_id, first_name, last_name, username, photo_url))

            # Снимаем флаг гостя и удаляем записи
            cursor.execute('DELETE FROM guest_signups WHERE user_telegram_id = (SELECT id FROM users WHERE telegram_id = ?)', (telegram_id,))
            cursor.execute('UPDATE users SET is_guest = 0 WHERE telegram_id = ?', (telegram_id,))

            self.conn.commit()
            logger.info(f"Гость {telegram_id} конвертирован в пользователя")
            return self.get_user_by_telegram_id(telegram_id)
        except Exception as e:
            logger.error(f"Ошибка конвертации гостя в пользователя: {e}")
            return None

    def delete_guest(self, telegram_id: int) -> Dict[str, Any]:
        """
        Удаление гостя и всех его записей

        Args:
            telegram_id: Telegram ID пользователя

        Returns:
            Dict с результатом операции
        """
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        try:
            # Сначала удаляем все записи из guest_signups
            cursor.execute('DELETE FROM guest_signups WHERE user_telegram_id = (SELECT id FROM users WHERE telegram_id = ?)', (telegram_id,))
            # Снимаем флаг гостя и удаляем пользователя
            cursor.execute('DELETE FROM users WHERE telegram_id = ? AND is_guest = 1', (telegram_id,))
            self.conn.commit()

            if cursor.rowcount > 0:
                return {"success": True, "message": "Гость и все его записи удалены"}
            else:
                return {"success": False, "error": "Гость не найден"}
        except Exception as e:
            logger.error(f"Ошибка удаления гостя: {e}")
            return {"success": False, "error": str(e)}

    # ==================== Методы для статистики тренировок ====================

    def get_training_stats(self, period: str = 'week') -> Dict[str, Any]:
        """
        Получение общей статистики по тренировкам за период

        Args:
            period: Период статистики ('day', 'week', 'month', 'all')

        Returns:
            Dict со статистикой:
                - total_trainings: количество тренировок
                - total_signups: общее количество записей
                - unique_users: количество уникальных пользователей
                - guests_count: количество гостей
                - users_count: количество авторизованных пользователей
                - avg_per_training: среднее количество участников на тренировку
                - date_range: диапазон дат (from, to)
        """
        if not self.conn:
            return {"error": "DB not connected"}

        cursor = self.conn.cursor()

        # Определяем диапазон дат
        date_filter, date_params = self._get_period_filter(period)

        # Общая статистика из event_signups (новая архитектура)
        cursor.execute(f'''
            SELECT 
                COUNT(DISTINCT e.id) as total_trainings,
                COUNT(es.id) as total_signups,
                COUNT(DISTINCT es.user_id) as unique_users,
                SUM(CASE WHEN es.is_guest = 1 THEN 1 ELSE 0 END) as guests_count,
                SUM(CASE WHEN es.is_guest = 0 THEN 1 ELSE 0 END) as users_count
            FROM events e
            INNER JOIN event_signups es ON e.id = es.event_id
            WHERE e.event_type IN ('training', 'scheduled_training', 'one_time_training')
              AND e.date {date_filter}
        ''', date_params if date_params else ())

        row = cursor.fetchone()
        stats = dict(row) if row else {}

        # Дополняем из training_registrations (старая архитектура)
        # только если нет данных из event_signups
        cursor.execute(f'''
            SELECT 
                COUNT(DISTINCT tr.training_date || tr.training_time || tr.chat_id) as total_trainings,
                COUNT(tr.id) as total_signups,
                COUNT(DISTINCT tr.user_telegram_id) as unique_users,
                0 as guests_count,
                COUNT(tr.id) as users_count
            FROM training_registrations tr
            INNER JOIN users u ON tr.user_telegram_id = u.telegram_id
            WHERE tr.registered_at {date_filter}
              AND u.is_active = 1
              AND NOT EXISTS (
                  SELECT 1 FROM event_signups es2
                  INNER JOIN events e2 ON es2.event_id = e2.id
                  WHERE e2.date = tr.training_date
                    AND e2.start_time = tr.training_time
                    AND e2.chat_id = tr.chat_id
              )
        ''', date_params if date_params else ())

        old_row = cursor.fetchone()
        if old_row:
            old_stats = dict(old_row)
            # Добавляем только если новые данные пустые
            if stats.get('total_trainings', 0) == 0:
                stats['total_trainings'] = old_stats.get('total_trainings', 0) or 0
            if stats.get('total_signups', 0) == 0:
                stats['total_signups'] = old_stats.get('total_signups', 0) or 0
            if stats.get('unique_users', 0) == 0:
                stats['unique_users'] = old_stats.get('unique_users', 0) or 0
            stats['users_count'] = (stats.get('users_count', 0) or 0) + (old_stats.get('users_count', 0) or 0)

        # Вычисляем среднее
        total_trainings = stats.get('total_trainings', 0) or 1
        stats['avg_per_training'] = round(stats.get('total_signups', 0) / total_trainings, 2)

        # Диапазон дат
        stats['date_range'] = self._get_period_date_range(period)
        stats['period'] = period

        return stats

    def get_training_details(self, training_date: str, training_time: str = None, chat_id: str = None) -> Dict[str, Any]:
        """
        Получение детальной информации о конкретной тренировке

        Args:
            training_date: Дата тренировки (YYYY-MM-DD)
            training_time: Время тренировки (опционально)
            chat_id: Chat ID (опционально)

        Returns:
            Dict с деталями тренировки:
                - training_info: информация о тренировке
                - participants: список участников
                - stats: статистика (users_count, guests_count, total)
        """
        if not self.conn:
            return {"error": "DB not connected"}

        cursor = self.conn.cursor()

        # Получаем информацию о тренировке из events
        cursor.execute('''
            SELECT uuid, name, date, start_time, end_time, location, chat_id, topic_id
            FROM events
            WHERE event_type IN ('training', 'scheduled_training', 'one_time_training')
              AND date = ?
              AND (? IS NULL OR start_time = ?)
              AND (? IS NULL OR chat_id = ?)
            ORDER BY start_time ASC
            LIMIT 1
        ''', (training_date, training_time, training_time, chat_id, chat_id))

        training_row = cursor.fetchone()

        if not training_row:
            # Пробуем найти в one_time_trainings или scheduled_trainings
            cursor.execute('''
                SELECT uuid, name, training_date as date, training_time as start_time, 
                       end_time, location, chat_id, topic_id
                FROM one_time_trainings
                WHERE training_date = ?
                  AND (? IS NULL OR training_time = ?)
                  AND (? IS NULL OR chat_id = ?)
                UNION ALL
                SELECT uuid, name, training_date as date, training_time as start_time,
                       end_time, location, chat_id, topic_id
                FROM scheduled_trainings
                WHERE training_date = ?
                  AND (? IS NULL OR training_time = ?)
                  AND (? IS NULL OR chat_id = ?)
                LIMIT 1
            ''', (training_date, training_time, training_time, chat_id, chat_id,
                  training_date, training_time, training_time, chat_id, chat_id))
            training_row = cursor.fetchone()

        if not training_row:
            return {"error": "Training not found"}

        training_info = dict(training_row)
        training_uuid = training_info.get('uuid')

        # Получаем участников из event_signups
        cursor.execute('''
            SELECT 
                u.telegram_id,
                u.first_name,
                u.last_name,
                u.username,
                es.status,
                es.is_guest,
                es.created_at as registered_at
            FROM event_signups es
            INNER JOIN users u ON es.user_id = u.id
            WHERE es.event_id = (SELECT id FROM events WHERE uuid = ?)
              AND u.is_active = 1
            ORDER BY es.created_at ASC
        ''', (training_uuid,))

        participants = [dict(row) for row in cursor.fetchall()]

        # Если участников нет, пробуем training_registrations
        if not participants:
            cursor.execute('''
                SELECT 
                    tr.user_telegram_id as telegram_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    tr.status,
                    0 as is_guest,
                    tr.registered_at
                FROM training_registrations tr
                INNER JOIN users u ON tr.user_telegram_id = u.telegram_id
                WHERE tr.training_date = ?
                  AND (? IS NULL OR tr.training_time = ?)
                  AND (? IS NULL OR tr.chat_id = ?)
                  AND u.is_active = 1
                ORDER BY tr.registered_at ASC
            ''', (training_date, training_time, training_time, chat_id, chat_id))
            participants = [dict(row) for row in cursor.fetchall()]

        # Статистика
        users_count = sum(1 for p in participants if not p.get('is_guest', False))
        guests_count = sum(1 for p in participants if p.get('is_guest', False))

        return {
            'training_info': training_info,
            'participants': participants,
            'stats': {
                'total': len(participants),
                'users_count': users_count,
                'guests_count': guests_count
            }
        }

    def get_user_stats(self, user_id: int, period: str = 'month') -> Dict[str, Any]:
        """
        Получение статистики по конкретному пользователю

        Args:
            user_id: Telegram ID пользователя
            period: Период статистики ('day', 'week', 'month', 'all')

        Returns:
            Dict со статистикой пользователя:
                - user_info: информация о пользователе
                - total_trainings: количество записей на тренировки
                - attended_trainings: количество посещённых тренировок (registered)
                - waitlist_count: количество записей в листе ожидания
                - guests_trainings: количество записей как гость
                - last_activity: дата последней активности
        """
        if not self.conn:
            return {"error": "DB not connected"}

        cursor = self.conn.cursor()

        # Получаем информацию о пользователе
        user = self.get_user_by_telegram_id(user_id)
        if not user:
            # Пробуем найти как гостя
            guest = self.get_guest_by_telegram(user_id)
            if guest:
                user = {
                    'telegram_id': guest['telegram_id'],
                    'first_name': guest['first_name'],
                    'last_name': guest.get('last_name'),
                    'username': guest.get('username'),
                    'is_guest': True
                }
            else:
                return {"error": "User not found"}

        # Определяем диапазон дат
        date_filter, date_params = self._get_period_filter(period)

        # Статистика из event_signups
        cursor.execute(f'''
            SELECT 
                COUNT(es.id) as total_trainings,
                SUM(CASE WHEN es.status = 'registered' THEN 1 ELSE 0 END) as attended_trainings,
                SUM(CASE WHEN es.status = 'waitlist' THEN 1 ELSE 0 END) as waitlist_count,
                SUM(CASE WHEN es.is_guest = 1 THEN 1 ELSE 0 END) as guests_trainings,
                MAX(es.created_at) as last_activity
            FROM event_signups es
            INNER JOIN events e ON es.event_id = e.id
            WHERE es.user_id = (SELECT id FROM users WHERE telegram_id = ?)
              AND e.event_type IN ('training', 'scheduled_training', 'one_time_training')
              AND e.date {date_filter}
        ''', [user_id] + (date_params if date_params else []))

        row = cursor.fetchone()
        stats = dict(row) if row else {}

        # Дополняем из training_registrations если нет данных
        if stats.get('total_trainings', 0) == 0:
            cursor.execute(f'''
                SELECT 
                    COUNT(tr.id) as total_trainings,
                    SUM(CASE WHEN tr.status = 'registered' THEN 1 ELSE 0 END) as attended_trainings,
                    SUM(CASE WHEN tr.status = 'waitlist' THEN 1 ELSE 0 END) as waitlist_count,
                    0 as guests_trainings,
                    MAX(tr.registered_at) as last_activity
                FROM training_registrations tr
                WHERE tr.user_telegram_id = ?
                  AND tr.registered_at {date_filter}
            ''', [user_id] + (date_params if date_params else []))
            
            old_row = cursor.fetchone()
            if old_row:
                stats = dict(old_row)

        # Заполняем нулями если None
        stats['total_trainings'] = stats.get('total_trainings', 0) or 0
        stats['attended_trainings'] = stats.get('attended_trainings', 0) or 0
        stats['waitlist_count'] = stats.get('waitlist_count', 0) or 0
        stats['guests_trainings'] = stats.get('guests_trainings', 0) or 0

        return {
            'user_info': user,
            'stats': stats,
            'period': period,
            'date_range': self._get_period_date_range(period)
        }

    def get_top_users(self, limit: int = 10, period: str = 'month') -> List[Dict[str, Any]]:
        """
        Получение топа пользователей по посещаемости

        Args:
            limit: Количество пользователей в топе
            period: Период статистики ('day', 'week', 'month', 'all')

        Returns:
            List пользователей с их статистикой:
                - telegram_id, first_name, last_name, username
                - total_trainings: количество записей
                - attended_trainings: количество посещений
                - guests_trainings: количество как гость
        """
        if not self.conn:
            return []

        cursor = self.conn.cursor()

        # Определяем диапазон дат
        date_filter, date_params = self._get_period_filter(period)

        # Топ из event_signups
        cursor.execute(f'''
            SELECT 
                u.telegram_id,
                u.first_name,
                u.last_name,
                u.username,
                u.is_guest,
                COUNT(es.id) as total_trainings,
                SUM(CASE WHEN es.status = 'registered' THEN 1 ELSE 0 END) as attended_trainings,
                SUM(CASE WHEN es.is_guest = 1 THEN 1 ELSE 0 END) as guests_trainings
            FROM event_signups es
            INNER JOIN events e ON es.event_id = e.id
            INNER JOIN users u ON es.user_id = u.id
            WHERE e.event_type IN ('training', 'scheduled_training', 'one_time_training')
              AND e.date {date_filter}
              AND u.is_active = 1
            GROUP BY u.id, u.telegram_id, u.first_name, u.last_name, u.username, u.is_guest
            ORDER BY total_trainings DESC, attended_trainings DESC
            LIMIT ?
        ''', date_params + [limit] if date_params else [limit])

        rows = [dict(row) for row in cursor.fetchall()]

        # Если нет данных, пробуем training_registrations
        if not rows:
            cursor.execute(f'''
                SELECT 
                    u.telegram_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    0 as is_guest,
                    COUNT(tr.id) as total_trainings,
                    SUM(CASE WHEN tr.status = 'registered' THEN 1 ELSE 0 END) as attended_trainings,
                    0 as guests_trainings
                FROM training_registrations tr
                INNER JOIN users u ON tr.user_telegram_id = u.telegram_id
                WHERE tr.registered_at {date_filter}
                  AND u.is_active = 1
                GROUP BY u.id, u.telegram_id, u.first_name, u.last_name, u.username
                ORDER BY total_trainings DESC, attended_trainings DESC
                LIMIT ?
            ''', date_params + [limit] if date_params else [limit])
            rows = [dict(row) for row in cursor.fetchall()]

        return rows

    def _get_period_filter(self, period: str) -> tuple:
        """
        Вспомогательный метод для получения SQL-фильтра по периоду

        Args:
            period: 'day', 'week', 'month', 'all'

        Returns:
            Tuple (filter_string, params)
        """
        from datetime import timedelta
        
        now = datetime.now()
        
        if period == 'day':
            start = now - timedelta(days=1)
            return (">= ?", [start.strftime('%Y-%m-%d')])
        elif period == 'week':
            start = now - timedelta(weeks=1)
            return (">= ?", [start.strftime('%Y-%m-%d')])
        elif period == 'month':
            start = now - timedelta(days=30)
            return (">= ?", [start.strftime('%Y-%m-%d')])
        else:  # 'all'
            return ("IS NOT NULL", [])

    def _get_period_date_range(self, period: str) -> Dict[str, str]:
        """
        Вспомогательный метод для получения диапазона дат периода

        Args:
            period: 'day', 'week', 'month', 'all'

        Returns:
            Dict с ключами 'from' и 'to'
        """
        from datetime import timedelta
        
        now = datetime.now()
        
        if period == 'day':
            start = now - timedelta(days=1)
            return {'from': start.strftime('%d.%m.%Y'), 'to': now.strftime('%d.%m.%Y')}
        elif period == 'week':
            start = now - timedelta(weeks=1)
            return {'from': start.strftime('%d.%m.%Y'), 'to': now.strftime('%d.%m.%Y')}
        elif period == 'month':
            start = now - timedelta(days=30)
            return {'from': start.strftime('%d.%m.%Y'), 'to': now.strftime('%d.%m.%Y')}
        else:  # 'all'
            return {'from': 'начало', 'to': now.strftime('%d.%m.%Y')}
