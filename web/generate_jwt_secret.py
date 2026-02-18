#!/usr/bin/env python3
"""
Скрипт для генерации безопасного JWT_SECRET
"""

import secrets
import os

# Генерируем случайную строку 32 байта (256 бит)
jwt_secret = secrets.token_urlsafe(32)

print("=" * 60)
print("Сгенерирован безопасный JWT_SECRET:")
print("=" * 60)
print(f"JWT_SECRET={jwt_secret}")
print("=" * 60)
print()

# Спрашиваем нужно ли сохранить в .env
env_file = os.path.join(os.path.dirname(__file__), '.env')
save = input(f"Сохранить в {env_file}? (y/n): ").strip().lower()

if save == 'y':
    # Читаем существующий .env
    existing = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing[key] = value
    
    # Обновляем JWT_SECRET
    existing['JWT_SECRET'] = jwt_secret
    
    # Записываем обратно
    with open(env_file, 'w') as f:
        for key, value in existing.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ JWT_SECRET сохранён в {env_file}")
    print("⚠️  Не забудьте перезапустить сервер!")
else:
    print("Скопируйте JWT_SECRET и добавьте в .env вручную")
