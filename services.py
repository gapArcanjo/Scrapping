"""
Camada de Use Cases — lógica de negócio pura.

Regras:
  - Apenas async: não bloqueia o event loop
  - Sem imports de FastAPI ou Celery aqui
  - with_for_update() previne race condition entre requests concorrentes
  - Idempotente: chamadas repetidas não geram efeitos duplicados
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Dispatch, Emergency, EmergencyStatus, Hospital, Responder


async def dispatch_emergency(emergency_id: int, db: AsyncSession) -> list[Dispatch]:
    """
    Encontra até 3 socorristas disponíveis e cria os despachos.

    with_for_update(skip_locked=True) garante que requests concorrentes
    não despachem o mesmo socorrista simultaneamente.
    """
    result = await db.execute(
        select(Emergency).where(Emergency.id == emergency_id).with_for_update()
    )
    emergency = result.scalar_one_or_none()

    if emergency is None:
        raise ValueError(f"Emergency {emergency_id} not found.")

    if emergency.status != EmergencyStatus.PENDING:
        return []  # já processada por outro request concorrente

    responder_result = await db.execute(
        select(Responder)
        .where(Responder.is_available == True)  # noqa: E712
        .with_for_update(skip_locked=True)
        .limit(3)
    )
    responders = responder_result.scalars().all()

    dispatches = []
    for responder in responders:
        # get_or_create manual — garante idempotência em retries do Celery
        existing = await db.execute(
            select(Dispatch).where(
                Dispatch.emergency_id == emergency_id,
                Dispatch.responder_id == responder.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            dispatch = Dispatch(emergency_id=emergency_id, responder_id=responder.id)
            db.add(dispatch)
            dispatches.append(dispatch)

    emergency.status = EmergencyStatus.DISPATCHED
    await db.flush()  # persiste sem commit (commit é feito pela session dependency)
    return dispatches


async def notify_hospitals(emergency_id: int, db: AsyncSession) -> list[Hospital]:
    """
    Retorna hospitais notificados.
    Em produção: filtrar por distância e enviar notificação real.
    """
    result = await db.execute(select(Emergency).where(Emergency.id == emergency_id))
    if result.scalar_one_or_none() is None:
        raise ValueError(f"Emergency {emergency_id} not found.")

    hospitals_result = await db.execute(select(Hospital).limit(2))
    return hospitals_result.scalars().all()


async def resolve_emergency(emergency_id: int, db: AsyncSession) -> bool:
    """
    Resolve a emergência. Retorna False se já estava resolvida.
    with_for_update evita double-resolve concorrente.
    """
    result = await db.execute(
        select(Emergency).where(Emergency.id == emergency_id).with_for_update()
    )
    emergency = result.scalar_one_or_none()

    if emergency is None:
        raise ValueError(f"Emergency {emergency_id} not found.")

    if emergency.status == EmergencyStatus.RESOLVED:
        return False

    emergency.status = EmergencyStatus.RESOLVED
    await db.flush()
    return True
