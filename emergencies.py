from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from auth import get_current_user
from services import resolve_emergency as resolve_emergency_service
from models import Emergency, User
from schemas import EmergencyCreate, EmergencyResponse
from events import EmergencyCreated, EmergencyResolved, publish

router = APIRouter(prefix="/emergencies", tags=["Emergencies"])


@router.get("/", response_model=list[EmergencyResponse])
async def list_emergencies(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Emergency).order_by(Emergency.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=EmergencyResponse, status_code=status.HTTP_201_CREATED)
async def create_emergency(
    body: EmergencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    emergency = Emergency(
        reporter_id=current_user.id,
        latitude=body.latitude,
        longitude=body.longitude,
        description=body.description,
    )
    db.add(emergency)
    await db.flush()  # obtém o id antes do commit

    publish(EmergencyCreated(
        emergency_id=emergency.id,
        latitude=float(emergency.latitude),
        longitude=float(emergency.longitude),
        description=emergency.description,
    ))

    return emergency


@router.get("/{emergency_id}", response_model=EmergencyResponse)
async def get_emergency(
    emergency_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Emergency).where(Emergency.id == emergency_id))
    emergency = result.scalar_one_or_none()
    if emergency is None:
        raise HTTPException(status_code=404, detail="Emergência não encontrada.")
    return emergency


@router.post("/{emergency_id}/resolve", response_model=EmergencyResponse)
async def resolve_emergency(
    emergency_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    resolved = await resolve_emergency_service(emergency_id, db)
    if not resolved:
        raise HTTPException(status_code=400, detail="Emergência já está resolvida.")

    publish(EmergencyResolved(emergency_id=emergency_id))

    result = await db.execute(select(Emergency).where(Emergency.id == emergency_id))
    return result.scalar_one()
