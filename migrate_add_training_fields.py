#!/usr/bin/env python3
"""
Миграция БД: Добавление новых полей в шаблоны тренировок
- start_time и end_time для poll_schedules
- start_time и end_time для one_time_trainings
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Добавляем поля в poll_schedules
    print("Обновление таблицы poll_schedules...")
    
    # start_time
    try:
        cursor.execute("ALTER TABLE poll_schedules ADD COLUMN start_time TEXT")
        print("  ✓ Добавлено поле start_time")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ Поле start_time уже существует")
        else:
            raise
    
    # end_time
    try:
        cursor.execute("ALTER TABLE poll_schedules ADD COLUMN end_time TEXT")
        print("  ✓ Добавлено поле end_time")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ Поле end_time уже существует")
        else:
            raise
    
    # Добавляем поля в one_time_trainings
    print("Обновление таблицы one_time_trainings...")
    
    # start_time
    try:
        cursor.execute("ALTER TABLE one_time_trainings ADD COLUMN start_time TEXT")
        print("  ✓ Добавлено поле start_time")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ Поле start_time уже существует")
        else:
            raise
    
    # end_time
    try:
        cursor.execute("ALTER TABLE one_time_trainings ADD COLUMN end_time TEXT")
        print("  ✓ Добавлено поле end_time")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ Поле end_time уже существует")
        else:
            raise

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена успешно!")
    print("\nПримечание: старые записи будут иметь NULL в полях start_time и end_time.")
    print("Для заполнения можно использовать training_time как start_time.")

if __name__ == "__main__":
    migrate()
