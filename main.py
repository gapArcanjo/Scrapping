"""
FastAPI app factory.

Responsabilidades:
  - Registrar middleware (audit, CORS, rate limit)
  - Montar routers por versão de API
  - Lifespan: inicializar e fechar conexões de forma limpa
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database import engine
from audit import AuditMiddleware
from logging_config import setup_logging
from rate_limiter import limiter

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Startup: verificações de saúde, conexões
    yield
    # Shutdown: fecha o pool de conexões com o banco
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,   # desativa Swagger em produção
        redoc_url="/redoc" if settings.debug else None,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Audit middleware (apenas rotas /api/v1/chat/)
    app.add_middleware(AuditMiddleware)

    # Routers
    from emergencies import router as emergencies_router
    from chat import router as chat_router

    app.include_router(emergencies_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()
