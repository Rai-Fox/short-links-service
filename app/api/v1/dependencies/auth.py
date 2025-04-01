from authx import RequestToken
from fastapi import Depends, HTTPException, Request, status

from authx.exceptions import MissingTokenError, JWTDecodeError

from db.repositories.users import UsersRepository, get_users_repository
from db.models.users import User
from api.v1.services.auth import AuthService

from core.security import get_security, TokenData
from core.logging import get_logger

logger = get_logger(__name__)


def get_auth_service(users_repository: UsersRepository = Depends(get_users_repository)) -> AuthService:
    return AuthService(users_repository=users_repository)


security = get_security()


# Вспомогательная зависимость для получения токена из запроса
async def _get_access_token_from_request_dependency(request: Request) -> RequestToken:
    """
    Internal dependency to extract the access token string using AuthX method.
    Returns None if the token is not found.
    """
    try:
        request_token = await security.get_access_token_from_request(request=request)
        return request_token
    except MissingTokenError:
        logger.debug("MissingTokenError caught by _get_access_token_from_request_dependency")
        return None


async def get_current_user(
    token: RequestToken | None = Depends(_get_access_token_from_request_dependency),
    users_repository: UsersRepository = Depends(get_users_repository),
) -> TokenData | None:
    """
    FastAPI dependency: Get current user from optional token.
    Verifies token and fetches user data asynchronously from DB. Returns None if no token or invalid.
    """

    if token is None:
        logger.debug("No token provided, returning None")
        return None

    username = security.verify_token(token=token).sub
    user: User | None = await users_repository.get_by_username(username=username)

    if user is None:
        logger.warning(f"Optional token valid for user {username}, but user not found in DB.")
        return None  # Treat as invalid/anonymous

    return TokenData(username=user.username)


async def get_required_current_user(
    token: RequestToken = Depends(security.get_access_token_from_request),
    users_repository: UsersRepository = Depends(get_users_repository),
) -> TokenData:
    """
    FastAPI dependency: Get current user from required token.
    Verifies token, fetches user data async from DB. Raises 401 HTTPException if invalid.
    """
    username = security.verify_token(token=token).sub
    user: User | None = await users_repository.get_by_username(username=username)

    if user is None:
        logger.error(f"Required token valid for user {username}, but user not found in DB.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenData(username=user.username)
