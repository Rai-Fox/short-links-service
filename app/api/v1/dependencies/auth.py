from fastapi import Depends

from db.repositories.users import UsersRepository, get_users_repository
from api.v1.services.auth import AuthService


def get_auth_service(users_repository: UsersRepository = Depends(get_users_repository)) -> AuthService:
    return AuthService(users_repository=users_repository)
