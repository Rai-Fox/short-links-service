from typing import Callable, Awaitable

from fastapi import Depends, Request

from authx import RequestToken

from db.repositories.users import UsersRepository, get_users_repository
from api.v1.services.auth import AuthService
from core.security import get_security, TokenData


def get_auth_service(users_repository: UsersRepository = Depends(get_users_repository)) -> AuthService:
    return AuthService(users_repository=users_repository)


TokenGetter = Callable[[Request], Awaitable[RequestToken]]

token_getter: TokenGetter = get_security().get_token_from_request(type="access", optional=True)

required_token_getter: TokenGetter = get_security().get_token_from_request(type="access", optional=False)


def get_current_user(
    request: Request,
    token: RequestToken | None = Depends(token_getter),
) -> TokenData | None:
    """
    Get the current user from the request token.
    """
    if token:
        return get_security().verify_token(token)
    return None


def get_required_current_user(
    request: Request,
    token: RequestToken = Depends(required_token_getter),
) -> TokenData:
    """
    Get the current user from the request token.
    """
    return get_security().verify_token(token)
