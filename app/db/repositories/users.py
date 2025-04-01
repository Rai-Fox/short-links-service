from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends

from db.repositories.base import BaseRepository
from db.models.users import User
from db import get_async_db_session

from core.logging import get_logger

logger = get_logger(__name__)


class UsersRepository(BaseRepository):
    async def get_by_username(self, username: str) -> User | None:
        """
        Get a user by username asynchronously.
        """
        logger.debug(f"Fetching user with username: {username}")
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return user

    async def create_user(self, username: str, hashed_password: str) -> User:
        """
        Create a new user asynchronously. Adds user to the session.
        Commit is handled by the session dependency.
        """
        logger.debug(f"Creating user with username: {username}")
        user = User(username=username, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        logger.info(f"User {username} added to session.")
        return user


def get_users_repository(
    session: AsyncSession = Depends(get_async_db_session),
) -> UsersRepository:
    """
    FastAPI dependency provider for UsersRepository.
    """
    return UsersRepository(session)
