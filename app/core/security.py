from datetime import datetime, timedelta, timezone

from authx import AuthX, AuthXConfig
from passlib.context import CryptContext
from pydantic import BaseModel

from core.config import get_settings
from core.logging import get_logger  # Добавим логгер для возможных предупреждений

logger = get_logger(__name__)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


auth_config = AuthXConfig(
    JWT_SECRET_KEY=get_settings().jwt_settings.SECRET_KEY,
    JWT_ALGORITHM=get_settings().jwt_settings.ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES=get_settings().jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_TOKEN_LOCATION=["headers"],
    JWT_HEADER_NAME="Authorization",
    JWT_HEADER_TYPE="Bearer",
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_security() -> AuthX:
    """Get the AuthX instance"""
    security = AuthX(config=auth_config)
    return security


def create_access_token(username: str, expires_delta: timedelta | None = None) -> str:
    """Create a new access token"""
    security = get_security()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=get_settings().jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    encoded_jwt = security.create_access_token(
        uid=username,
        expiry=expire,
    )
    return encoded_jwt


def get_password_hash(password: str) -> str:
    """Hash a plain password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)
