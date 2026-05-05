"""
Event Bus interno sobre Celery.

A view publica um evento de domínio e não sabe quem vai reagir.
Adicionar comportamento = novo handler com @on(Evento). Zero alteração existente.
"""
from dataclasses import asdict, dataclass

_REGISTRY: dict[str, list] = {}


@dataclass
class EmergencyCreated:
    emergency_id: int
    latitude: float
    longitude: float
    description: str


@dataclass
class EmergencyResolved:
    emergency_id: int


def on(event_class):
    """Registra uma Celery task como subscriber de um evento."""
    def decorator(task_func):
        _REGISTRY.setdefault(event_class.__name__, []).append(task_func)
        return task_func
    return decorator


def publish(event) -> None:
    """Dispara todas as tasks registradas para o evento."""
    for handler in _REGISTRY.get(type(event).__name__, []):
        handler.delay(asdict(event))
