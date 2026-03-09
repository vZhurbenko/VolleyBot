#!/usr/bin/env python3
"""
Проверка активных опросов в БД
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import Database

db = Database("volleybot.db")

print("=" * 60)
print("Активные опросы в БД")
print("=" * 60)

polls = db.get_active_polls()

if not polls:
    print("❌ Нет активных опросов")
    sys.exit(0)

print(f"Найдено опросов: {len(polls)}\n")

for poll in polls:
    print(f"📊 Опрос #{poll['id'][:8]}")
    print(f"   Chat ID: {poll['chat_id']}")
    print(f"   Message ID: {poll['message_id']}")
    print(f"   Topic ID: {poll.get('message_thread_id', 'N/A')}")
    print(f"   Template: {poll.get('template_id', 'N/A')}")
    print(f"   Создан: {poll['created_at']}")
    print()
