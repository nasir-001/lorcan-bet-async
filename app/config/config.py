from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production Settings"""

    app_name: str = "Lorcan bet async"
    environment: str = ""

    database_private_url: str
    # database settings
    postgres_user: str
    postgres_password: str
    postgres_db: str
    test_database_name: str
    database_private_address: str
    database_public_address: str
    # database_docker_address: str
    database_port: str

    # cors
    cors_origins: list[str] = []

    database_pool_size: int = 50
    database_max_overflow: int = 85

    model_config = SettingsConfigDict(
        env_file=(".env"),
        env_file_encoding="utf-8",
    )

settings = Settings()  # type: ignore
