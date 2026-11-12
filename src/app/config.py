import json
from typing import Annotated, Literal, Self

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ENV_PREFIX = "APP_"


class ConfigurationError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, env_file=".env", extra="ignore")

    # No default on purpose: the process refuses to start until someone picks one.
    environment: Literal["local", "staging", "production"]
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    cors_allow_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)
    cors_allow_credentials: bool = False
    cors_allow_methods: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["GET"])

    readiness_timeout_seconds: float = Field(default=2.0, gt=0)

    # Rate limiting is on by default so a missing middleware fails the readiness suite.
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=60, ge=1)
    rate_limit_window_seconds: float = Field(default=60.0, gt=0)
    # Number of reverse proxies in front of the app that append to X-Forwarded-For. At 0 the
    # header is ignored, because any client can send it and dodge the limiter.
    trusted_proxy_hops: int = Field(default=0, ge=0, le=10)

    # Empty DSN means Sentry stays off. Never required for boot.
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)

    # Empty means no SQLAlchemy engine is created. Alembic still ships with the template.
    database_url: str = ""
    database_ready_check: bool = False

    # How long shutdown waits for in-flight requests before disposing resources.
    shutdown_grace_seconds: float = Field(default=5.0, ge=0)

    @field_validator("cors_allow_origins", "cors_allow_methods", mode="before")
    @classmethod
    def _split_list(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        value = value.strip()
        if value.startswith("["):
            return json.loads(value)
        return [item.strip() for item in value.split(",") if item.strip()]

    @model_validator(mode="after")
    def _check_unsafe_combinations(self) -> Self:
        if self.cors_allow_credentials and "*" in self.cors_allow_origins:
            raise ValueError(
                "cors_allow_origins must not contain '*' while cors_allow_credentials is true; "
                "list the allowed origins explicitly"
            )
        if self.debug and self.environment == "production":
            raise ValueError("debug must be off when environment is 'production'")
        return self


def load_settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]  # required fields come from the environment
    except ValidationError as exc:
        lines = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            name = f"{ENV_PREFIX}{location}".upper() if location else "settings"
            if error["type"] == "missing":
                lines.append(f"  {name}: required but not set")
            else:
                lines.append(f"  {name}: {error['msg']}")
        raise ConfigurationError(
            "Invalid configuration, the app cannot start:\n" + "\n".join(lines)
        ) from None
