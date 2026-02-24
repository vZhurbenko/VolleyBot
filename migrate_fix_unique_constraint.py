#!/usr/bin/env python3
"""
Миграция БД: исправление UNIQUE ограничения в training_registrations

Было: UNIQUE(training_date, user_telegram_id)
Стало: UNIQUE(training_date, training_time, chat_id, user_telegram_id)

Это позволяет пользователю записываться на разные тренировки в один день
(например, утром и вечером)
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "volleybot.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # SQLite не позволяет изменить UNIQUE ограничение напрямую
    # Нужно пересоздать таблицу

    # 1. Переименовываем старую таблицу
    cursor.execute("ALTER TABLE training_registrations RENAME TO training_registrations_old")
    print("✓ Старая таблица переименована в training_registrations_old")

    # 2. Создаём новую таблицу с правильным ограничением
    cursor.execute("""
        CREATE TABLE training_registrations (
            id TEXT PRIMARY KEY,
            training_date DATE NOT NULL,
            training_time TEXT NOT NULL,
            chat_id TEXT NOT NULL,
            topic_id INTEGER,
            user_telegram_id INTEGER NOT NULL,
            status TEXT DEFAULT 'registered',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(training_date, training_time, chat_id, user_telegram_id)
        )
    """)
    print("✓ Создана новая таблица training_registrations с правильным UNIQUE ограничением")

    # 3. Копируем данные из старой таблицы в новую
    cursor.execute("""
        INSERT INTO training_registrations 
        (id, training_date, training_time, chat_id, topic_id, user_telegram_id, status, registered_at)
        SELECT id, training_date, training_time, chat_id, topic_id, user_telegram_id, status, registered_at
        FROM training_registrations_old
    """)
    print(f"✓ Скопировано {cursor.rowcount} записей")

    # 4. Удаляем старую таблицу
    cursor.execute("DROP TABLE training_registrations_old")
    print("✓ Старая таблица удалена")

    conn.commit()
    conn.close()

    print("\n✅ Миграция завершена успешно!")
    print("Теперь пользователь может записаться на несколько тренировок в один день")

if __name__ == "__main__":
    migrate()
