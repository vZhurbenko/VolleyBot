#!/usr/bin/env python3
"""
Миграция: Удаление поля end_time из таблицы games
"""

import sqlite3
import os
import sys
from pathlib import Path

DB_PATH = os.getenv("VOLLEYBOT_DB_PATH", "volleybot.db")


def migrate():
    """Удаление поля end_time из таблицы games"""
    print(f"Подключение к базе данных: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # В SQLite нет прямого DROP COLUMN, поэтому пересоздаём таблицу
    # 1. Получаем все данные
    cursor.execute("SELECT * FROM games")
    rows = cursor.fetchall()
    
    # 2. Переименовываем таблицу
    cursor.execute("ALTER TABLE games RENAME TO games_old")
    
    # 3. Создаём новую таблицу без end_time
    cursor.execute('''
        CREATE TABLE games (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT,
            start_time TEXT,
            opponent TEXT,
            chat_id TEXT,
            topic_id INTEGER,
            result TEXT,
            score TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Переносим данные (без end_time)
    if rows:
        # Старая схема: id, name, date, location, start_time, end_time, opponent, chat_id, topic_id, result, score, created_at, updated_at
        # Новая схема: id, name, date, location, start_time, opponent, chat_id, topic_id, result, score, created_at, updated_at
        for row in rows:
            cursor.execute('''
                INSERT INTO games (id, name, date, location, start_time, opponent, chat_id, topic_id, result, score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row[0],  # id
                row[1],  # name
                row[2],  # date
                row[3],  # location
                row[4],  # start_time
                row[6],  # opponent (пропускаем end_time который был row[5])
                row[7],  # chat_id
                row[8],  # topic_id
                row[9],  # result
                row[10], # score
                row[11], # created_at
                row[12]  # updated_at
            ))
    
    # 5. Удаляем старую таблицу
    cursor.execute("DROP TABLE games_old")
    
    conn.commit()
    conn.close()
    
    print("✅ Поле end_time успешно удалено из таблицы games")
    return True


if __name__ == "__main__":
    try:
        success = migrate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        sys.exit(1)
