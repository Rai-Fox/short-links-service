from fastapi import Depends

from core.logging import get_logger
from core.security import create_access_token, Token
from api.v1.schemas.auth import UserRegister, UserLogin, UserInDB
from api.v1.exceptions.auth import UserAlreadyExistsException, InvalidCredentialsException, UserNotFoundException
from db.repositories.users import UsersRepository, get_users_repository
from db.models.users import User

logger = get_logger(__name__)


class AuthService:
    def __init__(self, users_repository: UsersRepository = Depends(get_users_repository)):
        self.users_repository = users_repository

    async def register_user(self, user: UserRegister) -> Token:
        logger.info(f"Registering user: {user.username}")
        if await self.users_repository.get_by_username(user.username):
            logger.warning(f"User {user.username} already exists")
            raise UserAlreadyExistsException(f"User {user.username} already exists")

        await self.users_repository.create_user(user.username, user.hashed_password)
        logger.info(f"User {user.username} registered successfully")

        token = create_access_token(user.username)
        return Token(access_token=token, token_type="bearer")

    async def login_user(self, user: UserLogin) -> Token:
        logger.info(f"Logging in user: {user.username}")
        db_user: User = await self.users_repository.get_by_username(user.username)

        if not db_user:
            logger.warning(f"User {user.username} not found")
            raise UserNotFoundException(f"User {user.username} not found")

        db_user: UserInDB = UserInDB(
            username=db_user.username,
            hashed_password=db_user.hashed_password,
        )

        if not db_user.verify_password(user.password):
            logger.warning(f"Invalid credentials for user {user.username}")
            raise InvalidCredentialsException()

        token = create_access_token(user.username)
        logger.info(f"User {user.username} logged in successfully")

        return Token(access_token=token, token_type="bearer")
