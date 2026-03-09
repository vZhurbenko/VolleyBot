#!/usr/bin/env python3
"""
Миграция БД: Снятие NOT NULL ограничения с training_time в poll_schedules
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # SQLite не позволяет напрямую изменить NOT NULL, нужно пересоздать таблицу
    # Но мы можем обновить существующие записи, установив training_time
    
    print("Обновление записей в poll_schedules...")
    
    # Сначала обновим существующие записи, где training_time NULL
    cursor.execute("""
        UPDATE poll_schedules 
        SET training_time = COALESCE(training_time, start_time || ' - ' || end_time)
        WHERE training_time IS NULL AND start_time IS NOT NULL AND end_time IS NOT NULL
    """)
    
    # Для записей где start_time или end_time NULL, копируем из training_time
    cursor.execute("""
        UPDATE poll_schedules 
        SET start_time = SUBSTR(training_time, 1, INSTR(training_time, ' - ') - 1),
            end_time = SUBSTR(training_time, INSTR(training_time, ' - ') + 3)
        WHERE (start_time IS NULL OR end_time IS NULL) AND training_time LIKE '% - %'
    """)
    
    # Теперь снимаем NOT NULL ограничение с training_time
    # Для этого нужно пересоздать таблицу
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_schedules_new (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            message_thread_id INTEGER,
            training_day TEXT NOT NULL,
            poll_day TEXT NOT NULL,
            training_time TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            start_time TEXT,
            end_time TEXT,
            location TEXT
        )
    """)
    
    # Копируем данные
    cursor.execute("""
        INSERT INTO poll_schedules_new 
        SELECT * FROM poll_schedules
    """)
    
    # Удаляем старую таблицу
    cursor.execute("DROP TABLE poll_schedules")
    
    # Переименовываем новую
    cursor.execute("ALTER TABLE poll_schedules_new RENAME TO poll_schedules")
    
    conn.commit()
    conn.close()

    print("✅ Миграция завершена успешно!")

if __name__ == "__main__":
    migrate()
