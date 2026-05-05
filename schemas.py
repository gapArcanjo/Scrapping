"""
Schemas Pydantic v2 — contratos de entrada e saída da API.

Em FastAPI, o schema é o serializer, o validador e a documentação OpenAPI
ao mesmo tempo. Mantemos schemas de Request e Response separados:
Request valida entrada; Response controla o que expõe para fora.
"""
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models import EmergencyStatus

_INJECTION_RE = re.compile(
    r"ignore (previous|all|your) instructions?|you are now|pretend (you are|to be)"
    r"|forget (your )?(rules?|guidelines?)|DAN\b|act as if you have no",
    re.IGNORECASE,
)


# ── Emergency ──────────────────────────────────────────────────────────────────

class EmergencyCreate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    description: str = Field(..., min_length=3, max_length=1000)


class EmergencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reporter_id: Optional[int]
    latitude: float
    longitude: float
    description: str
    status: EmergencyStatus
    created_at: datetime
    updated_at: datetime


class EmergencyStatusUpdate(BaseModel):
    status: EmergencyStatus


# ── Chat ───────────────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=2000)
    session_id: Optional[UUID] = None

    @field_validator("message")
    @classmethod
    def reject_prompt_injection(cls, v: str) -> str:
        if _INJECTION_RE.search(v):
            raise ValueError("Mensagem contém conteúdo não permitido neste contexto médico.")
        return v.strip()


class ChatMessageResponse(BaseModel):
    reply: str
    session_id: Optional[UUID]


# ── Auth ───────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    email: str
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    is_active: bool
