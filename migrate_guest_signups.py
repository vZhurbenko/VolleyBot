#!/usr/bin/env python3
"""
Миграция: создание таблицы guest_signups для поддержки множественной записи гостей

Эта миграция:
1. Создаёт новую таблицу guest_signups
2. Переносит существующие записи из guests в guest_signups
3. Удаляет дубликаты (если гость записан на несколько тренировок)
4. Сохраняет обратную совместимость
"""

import sqlite3
import logging
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def migrate(db_path: str = "volleybot.db"):
    """Выполнение миграции"""
    print("=" * 60)
    print("🔄 Миграция guest_signups")
    print("=" * 60)
    print()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Создаём новую таблицу guest_signups если не существует
        print("📋 Создание таблицы guest_signups...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guest_signups (
                id TEXT PRIMARY KEY,
                guest_telegram_id INTEGER NOT NULL,
                training_uuid TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (guest_telegram_id) REFERENCES guests(telegram_id) ON DELETE CASCADE,
                FOREIGN KEY (training_uuid) REFERENCES games(uuid) ON DELETE CASCADE
            )
        ''')
        print("✅ Таблица guest_signups создана")

        # 2. Проверяем существующие записи в guests
        print("\n📊 Анализ существующих данных...")
        cursor.execute('SELECT COUNT(*) as count FROM guests')
        total_guests = cursor.fetchone()['count']
        print(f"   Всего гостей: {total_guests}")

        # 3. Переносим записи из guests в guest_signups
        print("\n📝 Перенос записей в guest_signups...")
        cursor.execute('''
            SELECT telegram_id, training_uuid, created_at FROM guests
            WHERE is_active = 1
        ''')
        existing_guests = cursor.fetchall()

        migrated_count = 0
        for guest in existing_guests:
            signup_id = f"signup_{guest['telegram_id']}_{guest['training_uuid']}"
            
            # Проверяем, существует ли уже запись
            cursor.execute('''
                SELECT id FROM guest_signups 
                WHERE guest_telegram_id = ? AND training_uuid = ?
            ''', (guest['telegram_id'], guest['training_uuid']))
            
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO guest_signups (id, guest_telegram_id, training_uuid, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (signup_id, guest['telegram_id'], guest['training_uuid'], guest['created_at']))
                migrated_count += 1

        print(f"✅ Перенесено записей: {migrated_count}")

        # 4. Проверяем наличие дубликатов (гости с несколькими записями)
        print("\n🔍 Проверка на дубликаты...")
        cursor.execute('''
            SELECT guest_telegram_id, COUNT(*) as count
            FROM guest_signups
            GROUP BY guest_telegram_id
            HAVING count > 1
        ''')
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"   Найдено гостей с несколькими записями: {len(duplicates)}")
            for dup in duplicates:
                print(f"   - Telegram ID {dup['guest_telegram_id']}: {dup['count']} тренировок")
        else:
            print("   Дубликатов не найдено")

        # 5. Создаём индексы для ускорения запросов
        print("\n📈 Создание индексов...")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_guest_signups_telegram 
            ON guest_signups(guest_telegram_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_guest_signups_training 
            ON guest_signups(training_uuid)
        ''')
        cursor.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_guest_signups_unique 
            ON guest_signups(guest_telegram_id, training_uuid)
        ''')
        print("✅ Индексы созданы")

        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ Миграция завершена успешно!")
        print("=" * 60)
        print()
        print("Сводка:")
        print(f"  - Создана таблица: guest_signups")
        print(f"  - Перенесено записей: {migrated_count}")
        print(f"  - Гостей с несколькими тренировками: {len(duplicates)}")
        print()
        print("📝 Следующие шаги:")
        print("   1. Обновить database.py")
        print("   2. Обновить API endpoints")
        print("   3. Обновить фронтенд")
        print()

    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка миграции: {e}")
        print(f"\n❌ Ошибка миграции: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
