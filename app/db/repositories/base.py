from sqlalchemy.ext.asyncio import AsyncSession
from core.logging import get_logger

logger = get_logger(__name__)


class BaseRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with an async database session.
        """
        self.session = session
