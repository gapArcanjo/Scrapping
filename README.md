# HealthTech Emergency Response

API de resposta a emergencias com FastAPI, SQLAlchemy async, Celery e Redis.

## Arquitetura alvo

Layout padronizado: **modulos na raiz**.

- `main.py`: bootstrap da API e middleware.
- `emergencies.py`, `chat.py`: camadas HTTP (routers).
- `auth.py`: autenticacao e injecao de dependencias.
- `services.py`: regras de negocio.
- `events.py`: publicacao de eventos de dominio.
- `worker.py`: app Celery.
- `handlers.py`: consumers de eventos (tasks).
- `database.py`, `models.py`, `schemas.py`: persistencia e contratos.

Fluxo principal:

1. HTTP request entra por router FastAPI.
2. Router valida schema e chama service.
3. Service persiste no Postgres.
4. Router publica evento em `events.publish(...)`.
5. Handler Celery consome evento e executa processamento assincrono.

## Execucao local

1. Copie `.env.example` para `.env` e ajuste segredos.
2. Suba stack:

```bash
docker compose up --build
```

API: `http://localhost:8000`

## Testes

- Unitarios: `tests/unit`
- Integracao (Postgres/Redis): `tests/integration`

Rodar tudo:

```bash
pytest
```

## Qualidade

- Lint/format: Ruff
- Hooks locais: pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

## Chat endpoint

`/api/v1/chat/message` esta marcado como **experimental** e nao substitui avaliacao clinica.
