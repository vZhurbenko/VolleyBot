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
    
    # Получаем ID администраторов
    admin_ids_input = input_with_default(
        "Введите ID администраторов через запятую",
        "118295767"
    )
    admin_ids = [int(x.strip()) for x in admin_ids_input.split(',') if x.strip()]
    
    if not admin_ids:
        print("❌ Должен быть хотя бы один администратор!")
        db.close()
        sys.exit(1)
    
    print(f"   Добавлены администраторы: {admin_ids}")
    db.set_admin_ids(admin_ids)
    
    print()
    print("Шаг 2: Шаблон опроса по умолчанию")
    print("-" * 40)
    
    # Название шаблона
    name = input_with_default("Название шаблона", "Волейбольный опрос")
    
    # Описание
    description = input_with_default(
        "Описание (используйте {date} и {time} для подстановки)",
        "Волейбол {date} {time} ВГАФК"
    )
    
    # День тренировки
    print("День тренировки:")
    print("  1) monday")
    print("  2) tuesday")
    print("  3) wednesday")
    print("  4) thursday")
    print("  5) friday")
    print("  6) saturday")
    print("  7) sunday")
    day_choice = input_with_default("Выберите день (1-7)", "7")
    days_map = {
        '1': 'monday', '2': 'tuesday', '3': 'wednesday', '4': 'thursday',
        '5': 'friday', '6': 'saturday', '7': 'sunday'
    }
    training_day = days_map.get(day_choice, 'sunday')
    
    # День создания опроса
    print("День создания опроса:")
    print("  1) monday")
    print("  2) tuesday")
    print("  3) wednesday")
    print("  4) thursday")
    print("  5) friday")
    print("  6) saturday")
    print("  7) sunday")
    day_choice = input_with_default("Выберите день (1-7)", "5")
    poll_day = days_map.get(day_choice, 'friday')
    
    # Время тренировки
    training_time = input_with_default("Время тренировки", "18:00")
    
    # Варианты ответов
    default_options = ["Буду", "Не буду", "Возможно"]
    print(f"Варианты ответов (дефолтные: {', '.join(default_options)})")
    print("Введите каждый вариант с новой строки (пустая строка для использования дефолтных):")
    options = []
    while True:
        line = input()
        if not line:
            break
        options.append(line.strip())
    if not options:
        options = default_options
    
    # Chat ID по умолчанию
    default_chat_id = input_with_default(
        "Chat ID для опросов по умолчанию",
        "-1002588984009"
    )
    
    # Topic ID
    default_topic_id_str = input_with_default("Topic ID (если есть)", "1159")
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
    print("Шаг 3: Расписания опросов")
    print("-" * 40)
    
    schedules = []
    
    # Первое расписание
    print("\nРасписание #1:")
    schedule_id_1 = "3d3670a6-2bf9-4b26-91cf-10fd203a33f0"
    schedule_1 = {
        "id": schedule_id_1,
        "name": input_with_default("  Название", "Расписание friday->tuesday"),
        "chat_id": input_with_default("  Chat ID", default_chat_id),
        "message_thread_id": int(input_with_default("  Topic ID", str(default_topic_id or 0))) or None,
        "training_day": input_with_default("  День тренировки", "friday"),
        "poll_day": input_with_default("  День создания опроса", "tuesday"),
        "training_time": input_with_default("  Время тренировки", "20:00 - 22:00"),
        "poll_time": input_with_default("  Время создания опроса", "12:00"),
        "enabled": True
    }
    schedules.append(schedule_1)
    print("   Расписание #1 сохранено")
    
    # Второе расписание
    print("\nРасписание #2:")
    schedule_id_2 = "b53b43f1-2629-4898-af7f-349217ab3fe0"
    schedule_2 = {
        "id": schedule_id_2,
        "name": input_with_default("  Название", "Расписание sunday->wednesday"),
        "chat_id": input_with_default("  Chat ID", default_chat_id),
        "message_thread_id": int(input_with_default("  Topic ID", str(default_topic_id or 0))) or None,
        "training_day": input_with_default("  День тренировки", "sunday"),
        "poll_day": input_with_default("  День создания опроса", "wednesday"),
        "training_time": input_with_default("  Время тренировки", "18:00-20:00"),
        "poll_time": input_with_default("  Время создания опроса", "12:00"),
        "enabled": True
    }
    schedules.append(schedule_2)
    print("   Расписание #2 сохранено")
    
    # Сохраняем расписания
    for schedule in schedules:
        db.add_poll_schedule(schedule)
    
    print()
    print("=" * 60)
    print("✅ Инициализация базы данных завершена успешно!")
    print("=" * 60)
    print()
    print("Сводка:")
    print(f"  Администраторы: {admin_ids}")
    print(f"  Шаблон: {template['name']}")
    print(f"  Расписаний: {len(schedules)}")
    print()
    print("Теперь можно запустить бота: ./start_bot.sh")
    print()
    
    db.close()


if __name__ == '__main__':
    main()
