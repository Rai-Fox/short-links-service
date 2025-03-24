from db.repositories.base import BaseRepository
from db.models.users import User

from core.logging import get_logger

logger = get_logger(__name__)


class UsersRepository(BaseRepository):
    async def get_by_username(self, username: str) -> dict | None:
        """
        Get a user by username.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug(f"Fetching user with username: {username}")
                user = session.query(User).filter(User.username == username).first()
                return user.__dict__ if user else None

    async def create_user(self, username: str, hashed_password: str) -> User:
        """
        Create a new user.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug(f"Creating user with username: {username}")
                user = User(username=username, hashed_password=hashed_password)
                session.add(user)
                session.commit()
                return user


def get_users_repository() -> UsersRepository:
    return UsersRepository()
