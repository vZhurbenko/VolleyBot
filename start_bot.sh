#!/bin/bash
# Скрипт для запуска бота в фоне с сохранением PID

# Переходим в директорию скрипта (независимо от того, откуда запущен)
cd "$(dirname "$0")" || exit 1

# Проверяем, не запущен ли уже бот
if [ -f "bot.pid" ]; then
    PID=$(cat bot.pid)
    if ps -p $PID > /dev/null; then
        echo "Бот уже запущен с PID: $PID"
        exit 1
    else
        # Файл PID существует, но процесс не запущен - удаляем файл
        rm -f bot.pid
    fi
fi

# Активируем виртуальное окружение и запускаем бота в фоне
source venv/bin/activate

# Очищаем старый лог
> bot_output.log

nohup python3 bot.py > bot_output.log 2>&1 &
BOT_PID=$!

# Ждём немного и проверяем, не упал ли бот сразу
sleep 1

# Проверяем, жив ли процесс
if ! ps -p $BOT_PID > /dev/null; then
    echo "❌ Ошибка при запуске бота!"
    echo ""
    cat bot_output.log
    exit 1
fi

# Сохраняем PID в файл
echo $BOT_PID > bot.pid

echo "Бот запущен в фоне с PID: $BOT_PID"
echo "Логи записываются в файл: bot_output.log"