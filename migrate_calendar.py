#!/usr/bin/env python3
"""
Миграция БД для календаря тренировок
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Добавляем поле is_active в users если нет
    try:
        cursor.execute("""
            ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1
        """)
        print("✓ Добавлено поле is_active в users")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("✓ Поле is_active уже существует")
        else:
            raise
    
    # Таблица записей на тренировки
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_registrations (
            id TEXT PRIMARY KEY,
            training_date DATE NOT NULL,
            training_time TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            topic_id INTEGER,
            user_telegram_id INTEGER NOT NULL,
            status TEXT DEFAULT 'registered',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(training_date, user_telegram_id)
        )
    """)
    print("✓ Создана таблица training_registrations")
    
    # Таблица разовых тренировок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS one_time_trainings (
            id TEXT PRIMARY KEY,
            training_date DATE NOT NULL,
            training_time TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            topic_id INTEGER,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Создана таблица one_time_trainings")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Миграция завершена успешно!")

if __name__ == "__main__":
    migrate()
