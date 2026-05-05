"""
Handlers de eventos - Celery tasks sincronas.

Workers Celery rodam em processos separados com seu proprio event loop.
Por isso usamos SQLAlchemy sincronico aqui (nao AsyncSession).
"""
import logging
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from events import EmergencyCreated, on
from models import Dispatch, Emergency, EmergencyStatus, Hospital, Responder
from worker import celery_app

logger = logging.getLogger("healthtech.handlers")

_DATABASE_URL = (
    f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER', 'healthtech_user')}"
    f":{os.environ.get('POSTGRES_PASSWORD', 'healthtech_password')}"
    f"@{os.environ.get('POSTGRES_HOST', 'localhost')}"
    f":{os.environ.get('POSTGRES_PORT', '5432')}"
    f"/{os.environ.get('POSTGRES_DB', 'healthtech_db')}"
)

_engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(bind=_engine)


def _get_session() -> Session:
    return _SessionLocal()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
@on(EmergencyCreated)
def handle_dispatch_responders(self, event: dict):
    try:
        with _get_session() as db:
            emergency = db.execute(
                select(Emergency).where(Emergency.id == event["emergency_id"])
            ).scalar_one_or_none()

            if not emergency or emergency.status != EmergencyStatus.PENDING:
                return

            responders = db.execute(
                select(Responder).where(Responder.is_available == True).limit(3)  # noqa: E712
            ).scalars().all()

            for responder in responders:
                existing = db.execute(
                    select(Dispatch).where(
                        Dispatch.emergency_id == emergency.id,
                        Dispatch.responder_id == responder.id,
                    )
                ).scalar_one_or_none()

                if existing is None:
                    db.add(Dispatch(emergency_id=emergency.id, responder_id=responder.id))

            emergency.status = EmergencyStatus.DISPATCHED
            db.commit()
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
@on(EmergencyCreated)
def handle_notify_hospitals(self, event: dict):
    try:
        with _get_session() as db:
            hospitals = db.execute(select(Hospital).limit(2)).scalars().all()
            for hospital in hospitals:
                logger.info(
                    "notify_hospital",
                    extra={"hospital": hospital.name, "emergency_id": event["emergency_id"]},
                )
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
@on(EmergencyCreated)
def handle_process_geo_data(self, event: dict):
    try:
        logger.info("process_geo_data", extra={"emergency_id": event["emergency_id"]})
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def generate_monthly_health_report():
    """Agendada via Celery Beat no painel admin."""
    logger.info("generate_monthly_health_report")
    return "Monthly health report generated."
