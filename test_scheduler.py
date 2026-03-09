#!/usr/bin/env python3
"""
Тестовый скрипт для проверки планировщика
Создаёт тренировку из расписания и вызывает API бота
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import Database
import asyncio
import httpx
from datetime import datetime, timedelta

db = Database("volleybot.db")

# 1. Проверяем расписания
print("=" * 60)
print("1. Проверяем расписания в БД")
print("=" * 60)
schedules = db.get_poll_schedules()
print(f"Найдено расписаний: {len(schedules)}")

if not schedules:
    print("❌ Нет расписаний для теста!")
    sys.exit(1)

for schedule in schedules:
    print(f"\n📋 Расписание: {schedule['name']}")
    print(f"   ID: {schedule['id']}")
    print(f"   День тренировки: {schedule['training_day']}")
    print(f"   Время: {schedule['start_time']} - {schedule['end_time']}")
    print(f"   Chat ID: {schedule['chat_id']}")
    print(f"   Topic ID: {schedule.get('message_thread_id')}")
    print(f"   Location: {schedule.get('location')}")

# 2. Проверяем, что будет создано через 3 дня
print("\n" + "=" * 60)
print("2. Проверяем, какие тренировки будут созданы через 3 дня")
print("=" * 60)

target_date = datetime.now() + timedelta(days=3)
target_date_str = target_date.strftime('%Y-%m-%d')
target_weekday = target_date.weekday()

day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
           'friday': 4, 'saturday': 5, 'sunday': 6}

print(f"Сегодня: {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A')})")
print(f"Через 3 дня: {target_date_str} ({target_date.strftime('%A')})")
print(f"День недели (число): {target_weekday}")

matching_schedules = []
for schedule in schedules:
    if not schedule.get('enabled', True):
        continue
    
    training_day = schedule.get('training_day', 'monday')
    schedule_weekday = day_map.get(training_day.lower(), -1)
    
    if schedule_weekday == target_weekday:
        matching_schedules.append(schedule)
        print(f"\n✅ Расписание '{schedule['name']}' подходит для создания!")

if not matching_schedules:
    print(f"\n⚠️ Нет расписаний на {target_date_str}")
    print("   Планировщик не создаст тренировки сегодня")
    sys.exit(0)

# 3. Проверяем, есть ли уже такие тренировки
print("\n" + "=" * 60)
print("3. Проверяем существующие тренировки")
print("=" * 60)

for schedule in matching_schedules:
    existing = db.get_scheduled_training_by_schedule_and_date(
        schedule['id'], target_date_str
    )
    if existing:
        print(f"⚠️ Тренировка '{schedule['name']}' на {target_date_str} УЖЕ существует")
    else:
        print(f"✓ Тренировка '{schedule['name']}' на {target_date_str} будет создана")

# 4. Запускаем создание тренировок (как планировщик)
print("\n" + "=" * 60)
print("4. Запускаем создание тренировок (эмуляция планировщика)")
print("=" * 60)

import uuid as uuid_module

bot_api_key = 'volleybot_secret_key'
bot_api_url = 'http://127.0.0.1:8001/api/create_poll'

async def create_training(schedule):
    """Создание тренировки и вызов API бота"""
    
    # Проверяем дубликат
    existing = db.get_scheduled_training_by_schedule_and_date(
        schedule['id'], target_date_str
    )
    if existing:
        print(f"⚠️ Пропускаем '{schedule['name']}' - уже существует")
        return
    
    # Генерируем ID
    training_id = f"sched_{schedule['id']}_{target_date_str}_{str(uuid_module.uuid4())[:8]}"
    
    # Получаем параметры
    start_time = schedule.get('start_time', '')
    end_time = schedule.get('end_time', '')
    training_time = f"{start_time} - {end_time}"
    chat_id = schedule.get('chat_id', '')
    topic_id = schedule.get('message_thread_id')
    name = schedule.get('name', 'Тренировка')
    location = schedule.get('location', '')
    
    # Добавляем в БД
    result = db.add_scheduled_training(
        training_id=training_id,
        schedule_id=schedule['id'],
        training_date=target_date_str,
        training_time=training_time,
        chat_id=chat_id,
        topic_id=topic_id,
        name=name,
        start_time=start_time,
        end_time=end_time,
        location=location
    )
    
    if not result.get('success'):
        print(f"❌ Ошибка добавления в БД: {result.get('error')}")
        return
    
    print(f"✓ Добавлено в БД: {training_id}")
    
    # Вызываем API бота
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                bot_api_url,
                json={
                    'chat_id': chat_id,
                    'topic_id': topic_id,
                    'training_date': target_date_str,
                    'start_time': start_time,
                    'end_time': end_time,
                    'location': location,
                    'name': name
                },
                headers={'X-API-Key': bot_api_key},
                timeout=30
            )
            api_result = response.json()
            
            if response.status_code == 200 and api_result.get('success'):
                print(f"✅ Опрос создан в Telegram! Message ID: {api_result['result']['message_id']}")
            else:
                print(f"❌ Ошибка API бота: {api_result}")
    except Exception as e:
        print(f"❌ Ошибка вызова API: {e}")

# Запускаем асинхронно
async def main():
    await asyncio.gather(*[create_training(s) for s in matching_schedules])

asyncio.run(main())

# 5. Проверяем результат
print("\n" + "=" * 60)
print("5. Итоговая проверка")
print("=" * 60)

scheduled_trainings = db.get_scheduled_trainings(
    target_date.year, target_date.month
)
print(f"Всего тренировок в календаре на {target_date_str}: {len(scheduled_trainings)}")

for training in scheduled_trainings:
    print(f"  - {training['name']} ({training['training_date']}, {training['training_time']})")

print("\n✅ Тест завершён!")
