"""
Модуль для валидации данных Telegram Login Widget
"""

import hmac
import hashlib
import logging
from typing import Dict, Any
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)


class TelegramAuth:
    """
    Класс для валидации данных от Telegram Login Widget
    """

    def __init__(self, bot_token: str):
        """
        Инициализация с токеном бота

        Args:
            bot_token: Токен вашего Telegram бота
        """
        self.bot_token = bot_token

    def _generate_secret_key(self) -> bytes:
        """
        Генерация секретного ключа из токена бота
        Для Telegram Login Widget используется алгоритм:
        Secret Key = SHA256(bot_token)
        """
        return hashlib.sha256(self.bot_token.encode('utf-8')).digest()

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Проверка валидности данных от Telegram

        Args:
            data: Словарь с данными от Telegram (включая hash)

        Returns:
            True если данные валидны, иначе False
        """
        # Копируем данные и извлекаем hash
        data_copy = data.copy()
        received_hash = data_copy.pop('hash', None)

        if not received_hash:
            logger.warning("Hash отсутствует в данных")
            return False

        # Сортируем и форматируем данные для проверки
        items = []
        for key, value in sorted(data_copy.items()):
            if value is not None:
                items.append(f"{key}={value}")

        data_string = "\n".join(items)

        # Вычисляем ожидаемый hash
        # Secret Key = SHA256(bot_token)
        # Hash = HMAC_SHA256(Secret Key, data_string)
        secret_key = self._generate_secret_key()
        computed_hash = hmac.new(
            key=secret_key,
            msg=data_string.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Сравниваем hash'и
        result = hmac.compare_digest(computed_hash, received_hash)
        if not result:
            logger.warning(f"Неверная подпись данных")
        return result

    def is_auth_date_valid(self, auth_date: int, max_age_seconds: int = 86400) -> bool:
        """
        Проверка времени авторизации

        Args:
            auth_date: Unix timestamp авторизации
            max_age_seconds: Максимально допустимый возраст запроса в секундах (по умолчанию 24 часа)

        Returns:
            True если данные не устарели, иначе False
        """
        now = datetime.now().timestamp()
        return (now - auth_date) <= max_age_seconds

    def parse_init_data(self, init_data: str) -> Dict[str, Any]:
        """
        Парсинг initData из строки запроса

        Args:
            init_data: Строка с данными от Telegram (обычно из URL или заголовка)

        Returns:
            Словарь с распарсенными данными
        """
        parsed_data = urllib.parse.parse_qs(init_data)
        # Преобразуем значения из списков в одиночные значения
        return {key: value[0] for key, value in parsed_data.items()}
