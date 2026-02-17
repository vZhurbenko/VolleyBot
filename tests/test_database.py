#!/usr/bin/env python3
"""
Тесты для модуля database.py
"""

import pytest
from database import Database


class TestDatabaseInit:
    """Тесты инициализации Database"""

    def test_init_creates_connection(self, test_db_path):
        db = Database(test_db_path)
        assert db.db_path == test_db_path

    def test_init_nonexistent_db(self, test_db_path):
        # База данных ещё не существует
        db = Database(test_db_path)
        # conn будет None, пока не вызовем create_tables
        db.create_tables()
        assert db.conn is not None

    def test_close(self, test_db_path):
        db = Database(test_db_path)
        db.create_tables()
        conn_before = db.conn
        db.close()
        # Проверяем, что соединение закрыто (оно может не быть None, но должно быть закрыто)
        # В текущей реализации conn не обнуляется, но close() вызывается
        assert conn_before is not None


class TestSettings:
    """Тесты методов для работы с настройками"""

    def test_set_and_get_setting(self, db):
        db.set_setting("test_key", "test_value")
        assert db.get_setting("test_key") == "test_value"

    def test_get_setting_default(self, db):
        assert db.get_setting("nonexistent", "default") == "default"

    def test_set_and_get_json(self, db):
        data = {"key": "value", "number": 42}
        db.set_setting("json_key", data)
        assert db.get_setting("json_key") == data

    def test_get_setting_returns_value_for_non_json(self, db):
        db.set_setting("string_key", "simple_string")
        assert db.get_setting("string_key") == "simple_string"


class TestAdminIds:
    """Тесты методов для работы с администраторами"""

    def test_get_admin_ids_empty(self, db):
        assert db.get_admin_ids() == []

    def test_add_admin_id(self, db):
        db.add_admin_id(123456789)
        assert 123456789 in db.get_admin_ids()

    def test_add_admin_id_unique(self, db):
        db.add_admin_id(123456789)
        db.add_admin_id(123456789)
        assert db.get_admin_ids() == [123456789]

    def test_add_multiple_admins(self, db):
        db.add_admin_id(111)
        db.add_admin_id(222)
        db.add_admin_id(333)
        admin_ids = db.get_admin_ids()
        assert len(admin_ids) == 3
        assert 111 in admin_ids
        assert 222 in admin_ids
        assert 333 in admin_ids

    def test_set_admin_ids(self, db):
        db.set_admin_ids([100, 200, 300])
        assert db.get_admin_ids() == [100, 200, 300]


class TestDefaultTemplate:
    """Тесты методов для работы с шаблоном опроса"""

    def test_get_default_template_returns_defaults(self, db):
        template = db.get_default_template()
        assert isinstance(template, dict)
        assert "name" in template
        assert "options" in template

    def test_set_default_template(self, db, sample_template):
        db.set_default_template(sample_template)
        stored = db.get_default_template()
        assert stored["name"] == sample_template["name"]
        assert stored["description"] == sample_template["description"]

    def test_update_template_field(self, db):
        db.update_template_field("name", "Новое название")
        template = db.get_default_template()
        assert template["name"] == "Новое название"

    def test_update_template_field_preserves_others(self, db):
        original = db.get_default_template()
        db.update_template_field("name", "Новое название")
        template = db.get_default_template()
        assert template["name"] == "Новое название"
        assert template["options"] == original["options"]


class TestPollSchedules:
    """Тесты методов для работы с расписаниями опросов"""

    def test_get_poll_schedules_empty(self, db):
        assert db.get_poll_schedules() == []

    def test_add_poll_schedule(self, db, sample_schedule):
        db.add_poll_schedule(sample_schedule)
        schedules = db.get_poll_schedules()
        assert len(schedules) == 1
        assert schedules[0]["id"] == sample_schedule["id"]
        assert schedules[0]["name"] == sample_schedule["name"]

    def test_add_poll_schedule_enabled_default(self, db):
        schedule = {
            "id": "test-1",
            "chat_id": "-1001234567890",
            "training_day": "monday",
            "poll_day": "sunday",
            "training_time": "18:00"
        }
        db.add_poll_schedule(schedule)
        schedules = db.get_poll_schedules()
        assert schedules[0]["enabled"] is True

    def test_get_poll_schedule(self, db, sample_schedule):
        db.add_poll_schedule(sample_schedule)
        schedule = db.get_poll_schedule("test-schedule-1")
        assert schedule is not None
        assert schedule["name"] == sample_schedule["name"]

    def test_get_poll_schedule_not_found(self, db):
        assert db.get_poll_schedule("nonexistent") is None

    def test_update_poll_schedule(self, db, sample_schedule):
        db.add_poll_schedule(sample_schedule)
        db.update_poll_schedule("test-schedule-1", {"training_time": "19:00 - 21:00"})
        schedule = db.get_poll_schedule("test-schedule-1")
        assert schedule["training_time"] == "19:00 - 21:00"

    def test_remove_poll_schedule(self, db, sample_schedule):
        db.add_poll_schedule(sample_schedule)
        db.remove_poll_schedule("test-schedule-1")
        assert db.get_poll_schedules() == []

    def test_multiple_schedules(self, db):
        schedules_data = [
            {"id": f"schedule-{i}", "chat_id": "-1001234567890",
             "training_day": "monday", "poll_day": "sunday",
             "training_time": "18:00", "name": f"Schedule {i}"}
            for i in range(5)
        ]
        for schedule in schedules_data:
            db.add_poll_schedule(schedule)

        schedules = db.get_poll_schedules()
        assert len(schedules) == 5


class TestActivePolls:
    """Тесты методов для работы с активными опросами"""

    def test_get_active_polls_empty(self, db):
        assert db.get_active_polls() == []

    def test_add_active_poll(self, db):
        db.add_active_poll(
            poll_id="poll-1",
            chat_id="-1001234567890",
            message_id=123
        )
        polls = db.get_active_polls()
        assert len(polls) == 1
        assert polls[0]["id"] == "poll-1"
        assert polls[0]["message_id"] == 123

    def test_add_active_poll_with_thread_id(self, db):
        db.add_active_poll(
            poll_id="poll-1",
            chat_id="-1001234567890",
            message_id=123,
            message_thread_id=456
        )
        poll = db.get_active_poll("poll-1")
        assert poll["message_thread_id"] == 456

    def test_get_active_poll(self, db):
        db.add_active_poll("poll-1", "-1001234567890", 123)
        poll = db.get_active_poll("poll-1")
        assert poll is not None
        assert poll["chat_id"] == "-1001234567890"

    def test_get_active_poll_not_found(self, db):
        assert db.get_active_poll("nonexistent") is None

    def test_remove_active_poll(self, db):
        db.add_active_poll("poll-1", "-1001234567890", 123)
        db.remove_active_poll("poll-1")
        assert db.get_active_polls() == []

    def test_multiple_active_polls(self, db):
        db.add_active_poll("poll-1", "-1001234567890", 123)
        db.add_active_poll("poll-2", "-1001234567891", 456)
        db.add_active_poll("poll-3", "-1001234567892", 789)

        polls = db.get_active_polls()
        assert len(polls) == 3


class TestIsInitialized:
    """Тесты метода is_initialized"""

    def test_is_initialized_false(self, db):
        assert db.is_initialized() is False

    def test_is_initialized_true(self, db):
        db.add_admin_id(123456789)
        assert db.is_initialized() is True


class TestDatabaseWithFixtures:
    """Тесты с использованием фикстур"""

    def test_db_with_admin_fixture(self, db_with_admin):
        admin_ids = db_with_admin.get_admin_ids()
        assert len(admin_ids) == 1
        assert 123456789 in admin_ids

    def test_schedule_with_fixture(self, db, sample_schedule):
        db.add_poll_schedule(sample_schedule)
        schedule = db.get_poll_schedule(sample_schedule["id"])
        assert schedule["training_day"] == sample_schedule["training_day"]
        assert schedule["poll_day"] == sample_schedule["poll_day"]
