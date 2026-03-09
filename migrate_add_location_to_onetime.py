#!/usr/bin/env python3
"""
Миграция БД: Добавление поля location в one_time_trainings
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Обновление таблицы one_time_trainings...")
    
    try:
        cursor.execute("ALTER TABLE one_time_trainings ADD COLUMN location TEXT")
        print("  ✓ Добавлено поле location")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ✓ Поле location уже существует")
        else:
            raise

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена успешно!")

if __name__ == "__main__":
    migrate()
