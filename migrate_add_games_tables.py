#!/usr/bin/env python3
"""
Миграция: Добавление таблиц для игр (games, game_signups)
"""

import sqlite3
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database

DB_PATH = os.getenv("VOLLEYBOT_DB_PATH", "volleybot.db")


def migrate():
    """Создание таблиц для игр"""
    print(f"Подключение к базе данных: {DB_PATH}")
    
    db = Database(DB_PATH)
    
    # Принудительно создаём подключение
    if not db.conn:
        db.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        db.conn.row_factory = sqlite3.Row
    
    # Создаём таблицы
    cursor = db.conn.cursor()
    
    # Таблица игр
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT,
            start_time TEXT,
            end_time TEXT,
            opponent TEXT,
            chat_id TEXT,
            topic_id INTEGER,
            result TEXT,
            score TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица записей на игры
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_signups (
            id TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            user_telegram_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'registered',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
            FOREIGN KEY (user_telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
        )
    ''')
    
    db.conn.commit()
    
    # Проверяем существование таблиц
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='games'
    """)
    games_exists = cursor.fetchone() is not None
    
    # Проверка таблицы game_signups
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='game_signups'
    """)
    signups_exists = cursor.fetchone() is not None
    
    if games_exists and signups_exists:
        print("✅ Таблицы для игр успешно созданы/существуют")
        print("  - games")
        print("  - game_signups")
    else:
        print("❌ Ошибка создания таблиц")
        if not games_exists:
            print("  - games: не создана")
        if not signups_exists:
            print("  - game_signups: не создана")
    
    db.close()
    return games_exists and signups_exists


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
