"""
Configuração centralizada via pydantic-settings.

Vantagem sobre os.environ direto:
  - Validação e tipagem no startup (falha cedo, não em runtime)
  - Valores default documentados no código
  - Autocompletar no IDE
"""
from functools import lru_cache
from pydantic import PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "HealthTech Emergency Response"
    debug: bool = False
    secret_key: str
    allowed_hosts: list[str] = ["*"]

    # Database (async)
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis / Celery
    redis_host: str = "localhost"
    redis_port: int = 6379

    # OpenAI (opcional)
    openai_api_key: str | None = None

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @model_validator(mode="after")
    def validate_production_settings(self):
        if not self.debug and self.secret_key.startswith("insecure"):
            raise ValueError("SECRET_KEY inválida para produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
