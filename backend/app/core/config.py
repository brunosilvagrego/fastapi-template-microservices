from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_HOST: str = "postgres"
    DB_PORT: int = 5432
    DB_DATABASE: str = "postgres"
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = "postgres"  # noqa: S105


settings = Settings()
