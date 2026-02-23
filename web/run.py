#!/usr/bin/env python3
"""
Скрипт для запуска веб-сервера авторизации VolleyBot
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print(f"🚀 Запуск сервера авторизации VolleyBot...")
    print(f"📍 Адрес: http://{host}:{port}")
    print(f"📂 Database: {os.getenv('VOLLEYBOT_DB_PATH', 'volleybot.db')}")
    print(f"🤖 Bot: @{os.getenv('TELEGRAM_BOT_USERNAME', '')}")
    print(f"\n⚠️  Для остановки нажмите Ctrl+C")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,  # Авто-перезагрузка при изменении кода
        reload_dirs=[".."],  # Следить также за родительской папкой
        log_level="info"
    )
