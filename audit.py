"""
Audit Middleware — rastreabilidade de interações médicas.

Implementado como ASGI middleware puro (não depende de FastAPI):
  - Loga metadados de toda request para /api/v1/chat/
  - Nunca loga o body — dados de saúde são sensíveis
  - Logs estruturados (JSON) prontos para Datadog / CloudWatch / Elastic
"""
import json
import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("healthtech.audit")

AUDITED_PREFIXES = ("/api/v1/chat/",)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not any(request.url.path.startswith(p) for p in AUDITED_PREFIXES):
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        user_id = getattr(request.state, "user_id", "anonymous")
        content_length = request.headers.get("content-length", 0)

        record = {
            "event": "medical_interaction",
            "user_id": user_id,
            "method": request.method,
            "path": request.url.path,
            "content_length": content_length,  # tamanho, nunca o conteúdo
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }

        if response.status_code >= 400:
            logger.warning(json.dumps(record))
        else:
            logger.info(json.dumps(record))

        return response
