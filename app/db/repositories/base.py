from core.config import get_settings
from core.logging import get_logger
from db import session, async_session

logger = get_logger(__name__)


class BaseRepository:
    def get_connection(self):
        """
        Returns a database connection.
        """
        return session()

    def get_async_connection(self):
        """
        Returns an async database connection.
        """
        return async_session()
