#!/bin/bash
# Скрипт для остановки бота по PID

# Переходим в директорию скрипта (независимо от того, откуда запущен)
cd "$(dirname "$0")" || exit 1

PID_FILE="bot.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Файл PID не найден. Бот, возможно, не запущен."
    exit 1
fi

BOT_PID=$(cat $PID_FILE)

if [ -z "$BOT_PID" ]; then
    echo "PID в файле пуст. Бот, возможно, не запущен."
    rm -f $PID_FILE
    exit 1
fi

# Проверяем, запущен ли процесс
if ps -p $BOT_PID > /dev/null; then
    echo "Останавливаю бота с PID: $BOT_PID"
    kill $BOT_PID
    
    # Ждем немного, чтобы процесс завершился корректно
    sleep 2
    
    # Проверяем, завершился ли процесс
    if ps -p $BOT_PID > /dev/null; then
        echo "Процесс не завершился, принудительно завершаю..."
        kill -9 $BOT_PID
    fi
    
    # Удаляем файл PID
    rm -f $PID_FILE
    echo "Бот остановлен."
else
    echo "Процесс с PID $BOT_PID не найден. Удаляю файл PID."
    rm -f $PID_FILE
fi