import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, or_

from db.models.links import Link
from db.repositories.base import BaseRepository
from core.logging import get_logger
from core.config import get_settings
from core.redis import get_redis_client

logger = get_logger(__name__)


class LinksRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self.unused_cleanup_time = get_settings().links_service_settings.UNUSED_LINKS_THRESHOLD

    async def get_link(self, short_code: str) -> dict | None:
        """
        Получить информацию о ссылке по короткому коду.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug(f"Fetching link with short_code: {short_code}")
                link = session.query(Link).filter(Link.short_code == short_code, Link.is_active).first()
                return (
                    {
                        "short_code": link.short_code,
                        "original_url": link.original_url,
                        "created_at": link.created_at,
                        "clicks": link.clicks,
                        "last_used_at": link.last_used_at,
                        "expires_at": link.expires_at,
                    }
                    if link
                    else None
                )

    async def create_link(
        self, short_code: str, original_url: str, created_by: str, expires_at: datetime | None = None
    ) -> None:
        """
        Создать новую короткую ссылку.
        При наличии параметра expires_at ссылка будет считаться недействительной после указанного времени.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug(f"Creating link with short_code: {short_code}")
                link = Link(
                    short_code=short_code, original_url=original_url, created_by=created_by, expires_at=expires_at
                )
                session.add(link)

    async def update_link(
        self, short_code: str, new_original_url: str | None, new_expires_at: datetime | None, updated_by: str | None
    ) -> None:
        """
        Обновить оригинальный URL для заданного короткого кода.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug(f"Updating link {short_code} with new URL: {new_original_url}")
                link = session.query(Link).filter(Link.short_code == short_code, Link.is_active).first()

                if not link:
                    logger.warning(f"Link with short_code {short_code} not found.")
                    raise ValueError(f"Link with short_code {short_code} not found.")

                if link.created_by != updated_by:
                    logger.warning(f"User {updated_by} is not authorized to update this link.")
                    raise PermissionError(f"User {updated_by} is not authorized to update this link.")

                link.original_url = new_original_url

                session.query(Link).filter(Link.short_code == short_code, Link.is_active).update(
                    {
                        "original_url": new_original_url if new_original_url else link.original_url,
                        "expires_at": new_expires_at if new_expires_at else link.expires_at,
                        "updated_at": datetime.now(timezone.utc),
                        "clicks": 0,  # TODO: Может быть и не нужно обнулять счетчик кликов? Зависит от бизнес требований
                    }
                )

    async def delete_link(self, short_code: str, delete_by: str) -> bool:
        """
        Удалить ссылку по короткому коду.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug(f"Deleting link with short_code: {short_code}")
                link = session.query(Link).filter(Link.short_code == short_code, Link.is_active).first()

                if not link:
                    logger.warning(f"Link with short_code {short_code} not found.")
                    return False

                if link.created_by != delete_by:
                    logger.warning(f"User {delete_by} is not authorized to delete this link.")
                    raise PermissionError(f"User {delete_by} is not authorized to delete this link.")

                session.delete(link)
                return True

    async def record_click(self, short_code: str) -> None:
        """
        Зафиксировать переход по ссылке: увеличить счетчик кликов
        и обновить время последнего использования.
        """
        with self.get_connection() as session:
            with session.begin():
                link = session.query(Link).filter(Link.short_code == short_code, Link.is_active).first()
                if link:
                    link.clicks += 1
                    link.last_used_at = datetime.now(timezone.utc)
                    session.query(Link).filter(Link.short_code == short_code, Link.is_active).update(
                        {
                            "clicks": link.clicks,
                            "last_used_at": link.last_used_at,
                        }
                    )

    async def get_link_stats(self, short_code: str, get_by: str | None) -> dict | None:
        """
        Получить статистику по ссылке:
        оригинальный URL, дата создания, количество переходов, дата последнего использования.
        """
        with self.get_connection() as session:
            with session.begin():
                if not get_by:
                    raise PermissionError("User is not authorized to get link stats.")

                logger.debug(f"Fetching stats for link with short_code: {short_code}")
                link = session.query(Link).filter(Link.short_code == short_code, Link.is_active).first()

                if not link:
                    logger.warning(f"Link with short_code {short_code} not found.")
                    return None

                if link.created_by != get_by:
                    logger.warning(f"User {get_by} is not authorized to get stats for this link.")
                    raise PermissionError(f"User {get_by} is not authorized to get stats for this link.")

                return {
                    "short_code": link.short_code,
                    "original_url": link.original_url,
                    "created_at": link.created_at,
                    "clicks": link.clicks,
                    "last_used_at": link.last_used_at,
                    "expires_at": link.expires_at,
                }

    async def search_by_original_url(self, original_url: str) -> list[dict]:
        """
        Поиск ссылок по оригинальному URL.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug(f"Searching links with original_url: {original_url}")
                links = session.query(Link).filter(Link.original_url == original_url, Link.is_active).all()
                return [
                    {
                        "short_code": link.short_code,
                        "original_url": link.original_url,
                        "created_at": link.created_at,
                        "created_by": link.created_by,
                        "clicks": link.clicks,
                        "last_used_at": link.last_used_at,
                        "expires_at": link.expires_at,
                    }
                    for link in links
                ]

    async def check_expired_links(self) -> None:
        """
        Проверить и удалить просроченные ссылки.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug("Checking for expired links")
                removed_short_codes = (
                    session.query(Link)
                    .filter(Link.expires_at.is_not(None), Link.expires_at < func.now())
                    .update(
                        {
                            "is_active": False,
                            "expires_at": None,
                            "updated_at": datetime.now(timezone.utc),
                        },
                        synchronize_session=False,
                    )
                    .returning(Link.short_code)
                    .all()
                )
                print(removed_short_codes)
                return [code["short_code"] for code in removed_short_codes]

    async def check_unused_links(self) -> None:
        """
        Проверить и удалить просроченные ссылки.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug("Checking for expired links")
                removed_short_codes = (
                    session.query(Link)
                    .filter(
                        Link.last_used_at.is_not(None),
                        Link.last_used_at < datetime.now(timezone.utc) - timedelta(minutes=self.unused_cleanup_time),
                    )
                    .update(
                        {
                            "is_active": False,
                            "expires_at": None,
                            "updated_at": datetime.now(timezone.utc),
                        }
                    )
                    .returning(Link.short_code)
                    .all()
                )
                return [code["short_code"] for code in removed_short_codes]

    async def get_expired_links(self) -> list[dict]:
        """
        Получить список всех просроченных ссылок.
        """
        with self.get_connection() as session:
            with session.begin():
                logger.debug("Fetching expired links")
                expired_links = session.query(Link).filter(Link.is_active == False).all()
                return [
                    {
                        "short_code": link.short_code,
                        "original_url": link.original_url,
                        "created_at": link.created_at,
                        "created_by": link.created_by,
                        "clicks": link.clicks,
                        "last_used_at": link.last_used_at,
                        "expires_at": link.expires_at,
                    }
                    for link in expired_links
                ]


def get_links_repository() -> LinksRepository:
    return LinksRepository()


async def clean_up_expired_links():
    """
    Запланированная задача для очистки просроченных ссылок.
    """
    links_repository = get_links_repository()
    redis_client = get_redis_client()
    while True:
        await asyncio.sleep(get_settings().links_service_settings.CLEANUP_LINKS_INTERVAL)
        removed_codes = await links_repository.check_expired_links()
        for code in removed_codes:
            logger.debug(f"Deleting expired link with short_code: {code}")
            redis_client.delete(code)


async def clean_up_unused_links():
    """
    Запланированная задача для очистки неиспользуемых ссылок.
    """
    links_repository = get_links_repository()
    redis_client = get_redis_client()
    while True:
        await asyncio.sleep(get_settings().links_service_settings.CLEANUP_LINKS_INTERVAL)
        removed_codes = await links_repository.check_unused_links()
        for code in removed_codes:
            logger.debug(f"Deleting unused link with short_code: {code}")
            redis_client.delete(code)
