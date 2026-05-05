from dataclasses import dataclass
from unittest.mock import Mock

import events


@dataclass
class DummyEvent:
    value: int


def test_publish_calls_registered_handlers(monkeypatch):
    delay_mock = Mock()
    fake_handler = type("H", (), {"delay": delay_mock})()
    monkeypatch.setattr(events, "_REGISTRY", {"DummyEvent": [fake_handler]})

    events.publish(DummyEvent(value=10))

    delay_mock.assert_called_once_with({"value": 10})


def test_on_registers_handler(monkeypatch):
    monkeypatch.setattr(events, "_REGISTRY", {})
    task = type("Task", (), {"delay": lambda self, payload: payload})()
    decorated = events.on(DummyEvent)(task)
    assert decorated is task
    assert "DummyEvent" in events._REGISTRY
    assert events._REGISTRY["DummyEvent"][0] is task


def test_emergency_created_has_subscribers_registered():
    # import side effect: handlers register Celery tasks via @on(...)
    import handlers  # noqa: F401

    subscribers = events._REGISTRY.get("EmergencyCreated", [])
    assert len(subscribers) >= 3
