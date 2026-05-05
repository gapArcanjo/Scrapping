"""
Endpoint /chat/message.

Rate limiting via slowapi (20 req/min por usuario autenticado).
Validacao medica e rejeicao de prompt injection via Pydantic schema.
Audit logging via AuditMiddleware (transparente para a rota).
"""
from fastapi import APIRouter, Depends, Request

from auth import get_current_user
from models import User
from rate_limiter import limiter
from schemas import ChatMessageRequest, ChatMessageResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    summary="Experimental endpoint",
)
@limiter.limit("20/minute")
async def chat_message(
    request: Request,
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Endpoint experimental. A resposta automatizada ainda nao substitui avaliacao clinica.
    """
    _ = request
    _ = current_user
    return ChatMessageResponse(
        reply=(
            "Endpoint experimental: triagem automatizada ainda em validacao clinica. "
            "Procure atendimento medico em caso de urgencia."
        ),
        session_id=body.session_id,
    )
