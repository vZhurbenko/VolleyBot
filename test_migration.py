#!/usr/bin/env python3
"""
Тестовый скрипт для проверки миграции данных из JSON в SQLite
"""

import json
import os
import sys

# Создаем тестовый data.json если не существует
if not os.path.exists('data.json'):
    test_data = {
        "admin": {
            "user_ids": [123456789, 987654321]
        },
        "default_poll_template": {
            "name": "Волейбольный опрос",
            "description": "Волейбол {date} {time} ВГАФК",
            "training_day": "sunday",
            "poll_day": "friday",
            "training_time": "18:00",
            "options": [
                "Буду",
                "Не буду",
                "Возможно"
            ],
            "enabled": True,
            "default_chat_id": "-1001234567890",
            "default_topic_id": None
        },
        "poll_schedules": [
            {
                "id": "test_schedule_1",
                "name": "Тестовое расписание",
                "chat_id": "-1001234567890",
                "message_thread_id": 42,
                "training_day": "wednesday",
                "poll_day": "monday",
                "training_time": "20:00",
                "enabled": True
            }
        ]
    }
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    print("✅ Создан тестовый файл data.json")

# Удаляем старую БД если существует
if os.path.exists('volleybot.db'):
    os.remove('volleybot.db')
    print("🗑️  Удалена старая база данных volleybot.db")

# Импортируем и тестируем
from database import Database

print("\n📊 Тестирование миграции данных из JSON в SQLite\n")

# Создаем базу данных
db = Database('volleybot.db')
print("✅ База данных создана")

# Выполняем миграцию
db.migrate_from_json('data.json')
print("✅ Миграция выполнена\n")

# Проверяем данные
print("📋 Проверка данных:")
print("-" * 40)

admin_ids = db.get_admin_ids()
print(f"Администраторы: {admin_ids}")

template = db.get_default_template()
print(f"Шаблон опроса: {template['name']}")
print(f"  - Описание: {template['description']}")
print(f"  - День тренировки: {template['training_day']}")
print(f"  - Время: {template['training_time']}")
print(f"  - Варианты: {template['options']}")

schedules = db.get_poll_schedules()
print(f"\nРасписания ({len(schedules)}):")
for schedule in schedules:
    print(f"  - {schedule['name']}: {schedule['training_day']} в {schedule['training_time']}")

# Проверяем is_initialized
print(f"\nБаза инициализирована: {db.is_initialized()}")

db.close()

print("\n✅ Все тесты пройдены!")
