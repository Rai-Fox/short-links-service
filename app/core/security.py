from datetime import datetime, timedelta, timezone

from authx import AuthX, AuthXConfig
from passlib.context import CryptContext
from pydantic import BaseModel

from core.config import get_settings
from db.repositories.users import get_users_repository


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


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
    security = AuthX(config=auth_config)

    @security.set_subject_getter
    def get_user_from_username(username) -> TokenData:
        user = get_users_repository().get_by_username(username)
        return TokenData(username=user.username) if user else None

    return security


def create_access_token(username: str, expires_delta: int | None = None, security: AuthX = get_security()) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=get_settings().jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    encoded_jwt = security.create_access_token(
        uid=username,
        expiry=expire,
        data={"username": username},
    )
    return encoded_jwt


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
