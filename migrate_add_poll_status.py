#!/usr/bin/env python3
"""
Миграция БД: Добавление поля status в active_polls
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Добавляем поле status
    cursor.execute('''
        ALTER TABLE active_polls ADD COLUMN status TEXT DEFAULT 'active'
    ''')
    print("✓ Добавлено поле status")

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена!")
    print("📝 Поле status: 'active' или 'stopped'")

if __name__ == "__main__":
    migrate()
