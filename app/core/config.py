from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class AppSettings(BaseSettings):
    NAME: str = "Short Links Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Short Links Service"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_prefix="APP_"
    )


class FastAPISettings(BaseSettings):
    HOST: str
    PORT: int

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_prefix="FASTAPI_"
    )


class RedisSettings(BaseSettings):
    HOST: str
    PORT: int
    DB: int = 0
    EXPIRES_IN_SECONDS: int = 5 * 60

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_prefix="REDIS_"
    )


class DatabaseSettings(BaseSettings):
    HOST: str
    PORT: int
    USER: str = Field(alias="db_user")
    PASSWORD: str = Field(alias="db_password")
    NAME: str
    TYPE: str = "postgresql"
    DRIVER: str = "psycopg2"
    ASYNC_DRIVER: str = "asyncpg"
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    ECHO: bool = False

    @property
    def CONNECTION_URL(self) -> str:
        if self.TYPE == 'sqlite':
            return f"{self.TYPE}:///:memory:"
        return f"{self.TYPE}+{self.DRIVER}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    @property
    def ASYNC_CONNECTION_URL(self) -> str:
        if self.TYPE == 'sqlite':
            return f"{self.TYPE}+{self.ASYNC_DRIVER}:///:memory:"
        return f"{self.TYPE}+{self.ASYNC_DRIVER}://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    model_config = ConfigDict(
        secrets_dir="/run/secrets",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_prefix="DATABASE_"
    )


class JWTSettings(BaseSettings):
    SECRET_KEY: str = Field(alias="jwt_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = ConfigDict(
        secrets_dir="/run/secrets",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_prefix="JWT_"
    )


class LinksServiceSettings(BaseSettings):
    GENERATE_SHORT_CODE_RETRIES: int = 5
    SHORT_CODE_LENGTH: int = 6
    CLEANUP_LINKS_INTERVAL: int = 30  # in seconds
    UNUSED_LINKS_THRESHOLD: int = 5   # in minutes

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        env_prefix="LINKS_SERVICE_"
    )


class Settings(BaseSettings):
    app_setings: AppSettings = AppSettings()
    fastapi_settings: FastAPISettings = FastAPISettings()
    redis_settings: RedisSettings = RedisSettings()
    db_settings: DatabaseSettings = DatabaseSettings()
    jwt_settings: JWTSettings = JWTSettings()
    links_service_settings: LinksServiceSettings = LinksServiceSettings()

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
