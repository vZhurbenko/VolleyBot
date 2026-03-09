#!/usr/bin/env python3
"""
Миграция БД: Удаление поля poll_day из poll_schedules
Опросы теперь создаются автоматически за 3 дня до тренировки
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # В SQLite нельзя удалить колонку напрямую, нужно пересоздать таблицу
    # 1. Создаём временную таблицу без poll_day
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_schedules_new (
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
    """)
    print("✓ Создана временная таблица poll_schedules_new")

    # 2. Копируем данные из старой таблицы в новую
    cursor.execute("""
        INSERT INTO poll_schedules_new (id, name, chat_id, message_thread_id,
                                        training_day, start_time, end_time, location, enabled,
                                        created_at, updated_at)
        SELECT id, name, chat_id, message_thread_id,
               training_day, start_time, end_time, location, enabled,
               created_at, updated_at
        FROM poll_schedules
    """)
    print("✓ Данные скопированы в новую таблицу")

    # 3. Удаляем старую таблицу
    cursor.execute("DROP TABLE poll_schedules")
    print("✓ Старая таблица poll_schedules удалена")

    # 4. Переименовываем новую таблицу
    cursor.execute("ALTER TABLE poll_schedules_new RENAME TO poll_schedules")
    print("✓ Таблица poll_schedules_new переименована в poll_schedules")

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена успешно!")
    print("📝 Поле poll_day удалено из poll_schedules")

if __name__ == "__main__":
    migrate()
