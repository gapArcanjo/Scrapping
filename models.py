"""
Modelos de domínio — SQLAlchemy 2.0 com anotações de tipo nativas.

Mapped[] elimina a ambiguidade entre coluna nullable e não-nullable
e habilita autocompletar correto no IDE sem plugins extras.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class EmergencyStatus(str, enum.Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    ON_SCENE = "ON_SCENE"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reported_emergencies: Mapped[list["Emergency"]] = relationship(back_populates="reporter")
    responder_profile: Mapped[Optional["Responder"]] = relationship(back_populates="user", uselist=False)


class Emergency(Base):
    __tablename__ = "emergencies"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float] = mapped_column(Numeric(9, 6))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[EmergencyStatus] = mapped_column(
        Enum(EmergencyStatus), default=EmergencyStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reporter: Mapped[Optional[User]] = relationship(back_populates="reported_emergencies")
    dispatches: Mapped[list["Dispatch"]] = relationship(back_populates="emergency", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Emergency(id={self.id}, status={self.status})"


class Responder(Base):
    __tablename__ = "responders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    specialty: Mapped[str] = mapped_column(String(100))
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)

    user: Mapped[User] = relationship(back_populates="responder_profile")
    dispatches: Mapped[list["Dispatch"]] = relationship(back_populates="responder")


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float] = mapped_column(Numeric(9, 6))
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)


class Dispatch(Base):
    __tablename__ = "dispatches"
    __table_args__ = (
        UniqueConstraint("emergency_id", "responder_id", name="uq_dispatch_emergency_responder"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    emergency_id: Mapped[int] = mapped_column(ForeignKey("emergencies.id", ondelete="CASCADE"))
    responder_id: Mapped[int] = mapped_column(ForeignKey("responders.id", ondelete="CASCADE"))
    dispatched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    emergency: Mapped[Emergency] = relationship(back_populates="dispatches")
    responder: Mapped[Responder] = relationship(back_populates="dispatches")
