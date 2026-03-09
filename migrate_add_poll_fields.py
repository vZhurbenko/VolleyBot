#!/usr/bin/env python3
"""
Миграция БД: Добавление полей в active_polls для отображения информации об опросе
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаём временную таблицу с новыми полями
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_polls_new (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            message_thread_id INTEGER,
            template_id TEXT,
            name TEXT,
            training_date TEXT,
            training_time TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Создана временная таблица active_polls_new")

    # Копируем данные из старой таблицы
    cursor.execute("""
        INSERT INTO active_polls_new (id, chat_id, message_id, message_thread_id, template_id, created_at)
        SELECT id, chat_id, message_id, message_thread_id, template_id, created_at
        FROM active_polls
    """)
    print("✓ Данные скопированы")

    # Удаляем старую таблицу
    cursor.execute("DROP TABLE active_polls")
    print("✓ Старая таблица удалена")

    # Переименовываем новую
    cursor.execute("ALTER TABLE active_polls_new RENAME TO active_polls")
    print("✓ Таблица переименована")

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена!")
    print("📝 Добавлены поля: name, training_date, training_time, location")

if __name__ == "__main__":
    migrate()
