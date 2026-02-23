#!/usr/bin/env python3
"""
Модуль для работы с SQLite базой данных
"""

import sqlite3
import json
import logging
import os
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
                        template_id: Optional[str] = None):
        """Добавление активного опроса"""
        if not self.conn:
            logger.error("Нельзя добавить активный опрос: база данных не подключена")
            return
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO active_polls (id, chat_id, message_id, message_thread_id, template_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (poll_id, chat_id, message_id, message_thread_id, template_id))
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

        # Таблица пользователей для веб-авторизации
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT,
                username TEXT,
                photo_url TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        self.conn.commit()
        logger.info("Таблицы базы данных созданы/проверены")

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
                INSERT INTO users (telegram_id, first_name, last_name, username, photo_url, is_admin, last_login)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
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

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()

        users = []
        for row in rows:
            user = dict(row)
            user['is_admin'] = bool(user['is_admin'])
            users.append(user)

        return users

    # ==================== Методы для работы с тренировками ====================

    def get_training_registrations(self, training_date: str, training_time: str, chat_id: str) -> List[Dict[str, Any]]:
        """Получение всех записей на тренировку"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tr.*, u.first_name, u.last_name, u.username, u.photo_url
            FROM training_registrations tr
            LEFT JOIN users u ON tr.user_telegram_id = u.telegram_id
            WHERE tr.training_date = ? AND tr.training_time = ? AND tr.chat_id = ?
            ORDER BY tr.registered_at ASC
        ''', (training_date, training_time, chat_id))
        
        return [dict(row) for row in cursor.fetchall()]

    def register_for_training(self, training_id: str, training_date: str, training_time: str, 
                              chat_id: str, topic_id: Optional[int], user_telegram_id: int) -> Dict[str, Any]:
        """Запись на тренировку с проверкой лимита (12 человек)"""
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
            cursor.execute('''
                INSERT OR REPLACE INTO training_registrations 
                (id, training_date, training_time, chat_id, topic_id, user_telegram_id, status, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (training_id, training_date, training_time, chat_id, topic_id, user_telegram_id, status))
            
            self.conn.commit()
            
            # Если только что записался в waitlist, проверяем не стал ли registered после замены
            if status == 'waitlist':
                # Проверяем текущий статус (мог измениться если кто-то отписался)
                cursor.execute('''
                    SELECT status FROM training_registrations
                    WHERE training_date = ? AND training_time = ? AND user_telegram_id = ?
                ''', (training_date, training_time, user_telegram_id))
                result = cursor.fetchone()
                status = result['status'] if result else 'waitlist'
            
            return {"success": True, "status": status}
        except Exception as e:
            logger.error(f"Ошибка записи на тренировку: {e}")
            return {"success": False, "error": str(e)}

    def unregister_from_training(self, training_date: str, training_time: str, 
                                 chat_id: str, user_telegram_id: int) -> Dict[str, Any]:
        """Отписка от тренировки с автоматическим зачислением из waitlist"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        
        try:
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
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка отписки от тренировки: {e}")
            return {"success": False, "error": str(e)}

    def get_user_trainings(self, user_telegram_id: int) -> List[Dict[str, Any]]:
        """Получение всех записей пользователя"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM training_registrations
            WHERE user_telegram_id = ?
            ORDER BY training_date ASC, training_time ASC
        ''', (user_telegram_id,))
        
        return [dict(row) for row in cursor.fetchall()]

    def add_one_time_training(self, training_id: str, training_date: str, training_time: str,
                              chat_id: str, topic_id: Optional[int], name: str) -> Dict[str, Any]:
        """Добавление разовой тренировки"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO one_time_trainings (id, training_date, training_time, chat_id, topic_id, name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (training_id, training_date, training_time, chat_id, topic_id, name))
            
            self.conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"Ошибка добавления разовой тренировки: {e}")
            return {"success": False, "error": str(e)}

    def remove_one_time_training(self, training_id: str) -> Dict[str, Any]:
        """Удаление разовой тренировки"""
        if not self.conn:
            return {"success": False, "error": "DB not connected"}

        cursor = self.conn.cursor()
        
        try:
            # Сначала удаляем все записи на эту тренировку
            cursor.execute('DELETE FROM training_registrations WHERE training_date = ? AND chat_id = ?',
                          (training_id.split('_')[0], training_id.split('_')[1] if '_' in training_id else None))
            
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

    def get_all_trainings(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Получение всех записей на тренировки за период (для админа)"""
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tr.*, u.first_name, u.last_name, u.username
            FROM training_registrations tr
            LEFT JOIN users u ON tr.user_telegram_id = u.telegram_id
            WHERE tr.training_date BETWEEN ? AND ?
            ORDER BY tr.training_date ASC, tr.training_time ASC, tr.registered_at ASC
        ''', (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]

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
                   creator.username as creator_username
            FROM invite_codes ic
            LEFT JOIN users creator ON ic.created_by = creator.telegram_id
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
            cursor.execute('''
                UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
            ''', (1 if is_active else 0, telegram_id))
            self.conn.commit()

            return {"success": True, "is_active": is_active}
        except Exception as e:
            logger.error(f"Ошибка переключения статуса: {e}")
            return {"success": False, "error": str(e)}
