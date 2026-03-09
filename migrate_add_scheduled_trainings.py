#!/usr/bin/env python3
"""
Миграция БД: Добавление таблицы scheduled_trainings для тренировок из расписаний
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаём таблицу для тренировок из расписаний
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_trainings (
            id TEXT PRIMARY KEY,
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
    """)
    print("✓ Создана таблица scheduled_trainings")

    # Создаём индекс для быстрого поиска по дате
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scheduled_trainings_date 
        ON scheduled_trainings(training_date)
    """)
    print("✓ Создан индекс на training_date")

    # Создаём индекс для поиска по schedule_id
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scheduled_trainings_schedule_id 
        ON scheduled_trainings(schedule_id)
    """)
    print("✓ Создан индекс на schedule_id")

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена успешно!")

if __name__ == "__main__":
    migrate()
