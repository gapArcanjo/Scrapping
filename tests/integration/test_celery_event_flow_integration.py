import os

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

import handlers  # noqa: F401 - registra subscribers via decorator
from events import EmergencyCreated, publish
from models import Dispatch, Emergency, EmergencyStatus, Responder, User
from worker import celery_app


def _sync_db_url() -> str:
    return (
        f"postgresql+psycopg2://{os.environ.get('POSTGRES_USER', 'healthtech_user')}"
        f":{os.environ.get('POSTGRES_PASSWORD', 'testpassword')}"
        f"@{os.environ.get('POSTGRES_HOST', 'localhost')}"
        f":{os.environ.get('POSTGRES_PORT', '5432')}"
        f"/{os.environ.get('POSTGRES_DB', 'healthtech_test')}"
    )


@pytest.mark.integration
def test_publish_emergency_created_triggers_dispatch_flow():
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    engine = create_engine(_sync_db_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as db:
        db.execute(delete(Dispatch))
        db.execute(delete(Responder))
        db.execute(delete(Emergency))
        db.execute(delete(User))
        db.commit()

        user = User(
            username="celery-int-user",
            email="celery-int-user@example.com",
            hashed_password="x",
            is_active=True,
        )
        db.add(user)
        db.flush()

        responder = Responder(
            user_id=user.id,
            specialty="Paramedic",
            is_available=True,
        )
        db.add(responder)

        emergency = Emergency(
            reporter_id=user.id,
            latitude=-23.55,
            longitude=-46.63,
            description="Acidente de transito",
            status=EmergencyStatus.PENDING,
        )
        db.add(emergency)
        db.commit()
        db.refresh(emergency)

        publish(
            EmergencyCreated(
                emergency_id=emergency.id,
                latitude=float(emergency.latitude),
                longitude=float(emergency.longitude),
                description=emergency.description,
            )
        )

        updated = db.execute(select(Emergency).where(Emergency.id == emergency.id)).scalar_one()
        dispatches = db.execute(select(Dispatch).where(Dispatch.emergency_id == emergency.id)).scalars().all()

        assert updated.status == EmergencyStatus.DISPATCHED
        assert len(dispatches) >= 1
