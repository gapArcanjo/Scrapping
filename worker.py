"""
Celery app — processo separado do FastAPI.

Celery workers são síncronos por design. Para acessar o banco de dados
dentro de uma task, usamos uma session síncrona separada (não AsyncSession).
"""
import os
from celery import Celery
from logging_config import setup_logging

os.environ.setdefault("APP_ENV", "production")
setup_logging()

celery_app = Celery(
    "healthtech",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=[os.environ.get("CELERY_INCLUDE", "handlers")],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_acks_late=True,           # confirma task só após execução bem-sucedida
    task_reject_on_worker_lost=True,  # recoloca na fila se o worker cair
)
