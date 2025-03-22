from functools import lru_cache
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    NAME: str = "Short Links Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Short Links Service"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"
        env_prefix = "APP_"


class FastAPISettings(BaseSettings):
    HOST: str
    PORT: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"
        env_prefix = "FASTAPI_"


class RedisSettings(BaseSettings):
    HOST: str
    PORT: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"
        env_prefix = "REDIS_"


class DatabaseSettings(BaseSettings):
    HOST: str
    PORT: int
    USER: str
    PASSWORD: str
    DB: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"
        env_prefix = "DATABASE_"


class JWTSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"
        env_prefix = "JWT_"


class Settings(BaseSettings):
    app_setings: AppSettings = AppSettings()
    fastapi_settings: FastAPISettings = FastAPISettings()
    # redis_settings: RedisSettings = RedisSettings()
    # postgresql_settings: PostgreSQLSettings = PostgreSQLSettings()
    # jwt_settings: JWTSettings = JWTSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
