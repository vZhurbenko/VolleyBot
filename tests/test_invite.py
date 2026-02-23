"""
Тесты для системы приглашений
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "volleybot.db"


@pytest.fixture
def db_connection():
    """Фикстура для подключения к БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def cleanup_invite_codes(db_connection):
    """Фикстура для очистки кодов после теста"""
    yield
    db_connection.execute('DELETE FROM invite_codes')
    db_connection.commit()


class TestInviteCodes:
    """Тесты для кодов приглашений"""

    def test_create_invite_code(self, db_connection, cleanup_invite_codes):
        """Тест создания кода приглашения"""
        from database import Database
        
        db = Database(DB_PATH)
        result = db.create_invite_code(
            code='test123',
            created_by=12345,
            expires_at=None
        )
        
        assert result['success'] is True
        assert result['code'] == 'test123'
        
        # Проверяем, что код сохранился в БД
        cursor = db_connection.execute(
            'SELECT * FROM invite_codes WHERE code = ?',
            ('test123',)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row['created_by'] == 12345
        assert row['enabled'] == 1

    def test_create_invite_code_with_expiry(self, db_connection, cleanup_invite_codes):
        """Тест создания кода с сроком действия"""
        from database import Database
        
        db = Database(DB_PATH)
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        result = db.create_invite_code(
            code='test_expiry',
            created_by=12345,
            expires_at=expires_at
        )
        
        assert result['success'] is True
        
        cursor = db_connection.execute(
            'SELECT expires_at FROM invite_codes WHERE code = ?',
            ('test_expiry',)
        )
        row = cursor.fetchone()
        assert row['expires_at'] is not None

    def test_get_invite_code(self, db_connection, cleanup_invite_codes):
        """Тест получения информации о коде"""
        from database import Database
        
        db = Database(DB_PATH)
        db.create_invite_code(code='test_get', created_by=12345)
        
        code_info = db.get_invite_code('test_get')
        
        assert code_info is not None
        assert code_info['code'] == 'test_get'
        assert code_info['created_by'] == 12345

    def test_get_nonexistent_invite_code(self, db_connection):
        """Тест получения несуществующего кода"""
        from database import Database
        
        db = Database(DB_PATH)
        code_info = db.get_invite_code('nonexistent')
        
        assert code_info is None

    def test_use_invite_code(self, db_connection, cleanup_invite_codes):
        """Тест использования кода"""
        from database import Database
        
        db = Database(DB_PATH)
        db.create_invite_code(code='test_use', created_by=12345)
        
        result = db.use_invite_code('test_use', telegram_id=67890)
        
        assert result is True
        
        # Проверяем, что код помечен как использованный
        code_info = db.get_invite_code('test_use')
        assert code_info['used_by'] == 67890
        assert code_info['enabled'] == 0

    def test_use_invite_code_twice_fails(self, db_connection, cleanup_invite_codes):
        """Тест повторного использования кода (должен fail)"""
        from database import Database
        
        db = Database(DB_PATH)
        db.create_invite_code(code='test_double', created_by=12345)
        
        # Первое использование
        result1 = db.use_invite_code('test_double', telegram_id=67890)
        assert result1 is True
        
        # Второе использование (должно fail)
        result2 = db.use_invite_code('test_double', telegram_id=11111)
        assert result2 is False

    def test_deactivate_invite_code(self, db_connection, cleanup_invite_codes):
        """Тест деактивации кода"""
        from database import Database
        
        db = Database(DB_PATH)
        db.create_invite_code(code='test_deactivate', created_by=12345)
        
        result = db.deactivate_invite_code('test_deactivate')
        
        assert result is True
        
        code_info = db.get_invite_code('test_deactivate')
        assert code_info['enabled'] == 0

    def test_get_all_invite_codes(self, db_connection, cleanup_invite_codes):
        """Тест получения всех кодов"""
        from database import Database
        
        db = Database(DB_PATH)
        db.create_invite_code(code='test_all_1', created_by=12345)
        db.create_invite_code(code='test_all_2', created_by=12345)
        
        codes = db.get_all_invite_codes()
        
        assert len(codes) >= 2
        codes_list = [c['code'] for c in codes]
        assert 'test_all_1' in codes_list
        assert 'test_all_2' in codes_list

    def test_expired_code_still_retrievable(self, db_connection, cleanup_invite_codes):
        """Тест получения истёкшего кода"""
        from database import Database
        
        db = Database(DB_PATH)
        expired_at = (datetime.now() - timedelta(days=1)).isoformat()
        
        db.create_invite_code(
            code='test_expired',
            created_by=12345,
            expires_at=expired_at
        )
        
        code_info = db.get_invite_code('test_expired')
        
        assert code_info is not None
        assert code_info['code'] == 'test_expired'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
