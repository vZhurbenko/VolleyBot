#!/usr/bin/env python3
"""
Скрипт для интерактивной инициализации базы данных бота
"""

import sys
import json
import logging

from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def input_with_default(prompt: str, default: str = "") -> str:
    """Запрос ввода с дефолтным значением"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    value = input(full_prompt).strip()
    return value if value else default


def input_list(prompt: str, default: list = None) -> list:
    """Запрос списка значений (каждое с новой строки)"""
    if default:
        print(f"{prompt} (дефолтные значения: {', '.join(default)})")
        print("Введите новые значения, каждое с новой строки (пустая строка для использования дефолтных):")
    else:
        print(f"{prompt} (введите значения, каждое с новой строки, пустая строка для завершения):")
    
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line.strip())
    
    return lines if lines else default


def main():
    """Основная функция инициализации"""
    print("=" * 60)
    print("🏐 Инициализация базы данных VolleyBot")
    print("=" * 60)
    print()

    db = Database("volleybot.db")
    
    # Создаём таблицы если не существуют
    db.create_tables()

    # Проверяем, не инициализирована ли уже база
    if db.is_initialized():
        print("⚠️  База данных уже инициализирована!")
        print(f"   Администраторы: {db.get_admin_ids()}")
        print()
        response = input("Продолжить и перезаписать данные? (y/N): ").strip().lower()
        if response != 'y':
            print("Инициализация отменена.")
            db.close()
            return
    
    print()
    print("Шаг 1: Настройка администраторов")
    print("-" * 40)
    print("Введите Telegram ID администраторов через запятую")
    print("(чтобы узнать свой ID, отправьте @userinfobot команду /start)")
    print()

    # Получаем ID администраторов
    while True:
        admin_ids_input = input("Telegram ID администраторов: ").strip()
        if admin_ids_input:
            break
        print("❌ Должен быть хотя бы один администратор!")
    
    admin_ids = [int(x.strip()) for x in admin_ids_input.split(',') if x.strip()]
    
    print(f"   Добавлены администраторы: {admin_ids}")
    db.set_admin_ids(admin_ids)
    
    print()
    print("Шаг 2: Шаблон опроса по умолчанию")
    print("-" * 40)

    # Название шаблона
    name = input_with_default("Название шаблона", "Волейбольный опрос")

    # Место проведения тренировки
    location = input("Место проведения тренировки: ").strip()
    if not location:
        print("❌ Место проведения не может быть пустым!")
        db.close()
        sys.exit(1)
    
    # Формируем описание
    description = f"Волейбол {{date}} {{time}} {location}"
    
    # День тренировки - понедельник
    training_day = 'monday'

    # День создания опроса - вторник
    poll_day = 'tuesday'

    # Время тренировки
    print("Время тренировки в формате чч:мм - чч:мм (например, 18:00 - 20:00)")
    training_time = input("Время тренировки: ").strip()
    if not training_time:
        print("❌ Время тренировки не может быть пустым!")
        db.close()
        sys.exit(1)
    
    # Варианты ответов
    default_options = ["Буду", "Не буду", "Возможно"]
    print(f"Пример: Буду, Не буду, Возможно")
    options_input = input("Варианты ответов через ', ' (запятая и пробел между вариантами): ").strip()
    if options_input:
        options = [opt.strip() for opt in options_input.split(', ')]
    else:
        options = default_options
    
    if len(options) < 2:
        print("❌ Должно быть хотя бы 2 варианта ответа!")
        db.close()
        sys.exit(1)

    # Chat ID по умолчанию — обязательно
    while True:
        default_chat_id = input("Chat ID для опросов по умолчанию: ").strip()
        if default_chat_id:
            break
        print("❌ Chat ID обязателен!")

    # Topic ID — опционально
    default_topic_id_str = input("Topic ID (если есть, нажмите Enter для пропуска): ").strip()
    default_topic_id = int(default_topic_id_str) if default_topic_id_str.isdigit() else None
    
    template = {
        "name": name,
        "description": description,
        "training_day": training_day,
        "poll_day": poll_day,
        "training_time": training_time,
        "options": options,
        "enabled": True,
        "default_chat_id": default_chat_id,
        "default_topic_id": default_topic_id
    }

    db.set_default_template(template)
    print(f"   Шаблон сохранён: {name}")

    print()
    print("=" * 60)
    print("✅ Инициализация базы данных завершена успешно!")
    print("=" * 60)
    print()
    print("Сводка:")
    print(f"  Администраторы: {admin_ids}")
    print(f"  Шаблон: {template['name']}")
    print(f"  День тренировки: {training_day}")
    print(f"  День создания опроса: {poll_day}")
    print()
    print("📝 Расписания можно настроить через бота в Telegram")
    print()
    print("Теперь можно запустить бота: ./start_bot.sh")
    print()

    db.close()


if __name__ == '__main__':
    main()
