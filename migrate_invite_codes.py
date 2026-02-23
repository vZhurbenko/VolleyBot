#!/usr/bin/env python3
"""
Миграция: Создание таблицы invite_codes для системы приглашений
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invite_codes (
            code TEXT PRIMARY KEY,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            used_by INTEGER,
            used_at TIMESTAMP,
            enabled BOOLEAN DEFAULT TRUE
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ Таблица invite_codes создана")


if __name__ == "__main__":
    migrate()
