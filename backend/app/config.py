from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration, overridable via environment variables (.env)."""

    app_name: str = "Signalwork API"
    environment: str = "development"
    log_level: str = "INFO"

    # Real Postgres by default. SQLite is intentionally NOT supported here —
    # the schema uses server-side constraints/indexes that behave differently
    # across engines, and testing on a different DB than production hides bugs.
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/signalwork"

    jwt_secret: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24h

    default_page_size: int = 20
    max_page_size: int = 100

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
