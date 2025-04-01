import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import update, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func, or_
from fastapi import Depends

from db.models.links import Link
from db.repositories.base import BaseRepository
from api.v1.schemas.links import LinkInDB
from core.logging import get_logger
from core.config import get_settings
from core.redis import get_redis_client
from db import get_async_db_session, async_session_factory

logger = get_logger(__name__)


class LinksRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.redis_cache = get_redis_client()
        self.unused_cleanup_time = get_settings().links_service_settings.UNUSED_LINKS_THRESHOLD

    async def get_link_by_short_code(self, short_code: str) -> Link | None:
        """Helper to fetch active Link object by short_code from DB"""
        logger.debug(f"Fetching link object with short_code: {short_code}")
        stmt = select(Link).where(Link.short_code == short_code, Link.is_active == True)
        result = await self.session.execute(stmt)
        link = result.scalar_one_or_none()
        return link

    async def get_link(self, short_code: str) -> dict | None:
        """
        Get link info by short_code (async). Checks cache first, then DB.
        Returns a dictionary representation.
        """
        logger.info(f"Try to find link with short_code={short_code} in cache")
        cached_link = self.get_original_link_from_cache(short_code)
        if cached_link:
            logger.debug(f"Link found in cache: {cached_link}")
            return cached_link.model_dump()

        logger.info(f"Link not found in cache, fetching from database for {short_code}")
        link = await self.get_link_by_short_code(short_code)

        if link:
            link_in_db = LinkInDB(
                short_code=link.short_code,
                original_url=str(link.original_url),
                created_at=link.created_at,
                clicks=link.clicks,
                last_used_at=link.last_used_at,
                expires_at=link.expires_at,
                created_by=link.created_by,
            )
            logger.debug(f"Setting link to cache: {link_in_db}")
            self.set_link_to_cache(short_code, link_in_db)
            return link_in_db.model_dump()
        else:
            logger.debug(f"Link with short_code {short_code} not found in DB.")
            return None

    async def create_link(
        self,
        short_code: str,
        original_url: str,
        created_by: str | None,
        expires_at: datetime | None = None,
    ) -> Link:
        """
        Create a new short link (async). Returns the Link object.
        """
        logger.debug(f"Creating link with short_code: {short_code}")
        link = Link(
            short_code=short_code,
            original_url=original_url,
            created_by=created_by,
            expires_at=expires_at,
            is_active=True,
            last_used_at=None,
        )
        self.session.add(link)
        await self.session.flush()
        await self.session.refresh(link)
        logger.info(f"Link {short_code} added to session.")
        return link

    async def update_link(
        self,
        short_code: str,
        new_original_url: str | None,
        new_expires_at: datetime | None,
        updated_by: str | None,
    ) -> Link | None:
        """
        Update original_url and/or expires_at for a given short_code (async).
        Returns the updated Link object or None if not found/updated.
        """
        logger.debug(f"Updating link {short_code} with new URL: {new_original_url}, expires: {new_expires_at}")

        link = await self.get_link_by_short_code(short_code)

        if not link:
            logger.warning(f"Link with short_code {short_code} not found.")
            raise ValueError(f"Link with short_code {short_code} not found.")

        # Permission check
        if link.created_by is not None and link.created_by != updated_by:
            logger.warning(
                f"User {updated_by} is not authorized to update link {short_code} created by {link.created_by}."
            )
            raise PermissionError(f"User {updated_by} is not authorized to update this link.")

        update_values = {
            "updated_at": datetime.now(timezone.utc),
            "clicks": 0,  # TODO: Может быть и не нужно обнулять счетчик кликов? Зависит от бизнес требований
        }
        if new_original_url is not None:
            update_values["original_url"] = new_original_url
        if new_expires_at is not None:
            update_values["expires_at"] = new_expires_at
        else:
            # If None is explicitly passed, set it to NULL in DB
            update_values["expires_at"] = None

        stmt = (
            update(Link)
            .where(Link.short_code == short_code, Link.is_active == True)
            .values(**update_values)
            .returning(Link)  # Return the updated link object
        )
        result = await self.session.execute(stmt)
        updated_link = result.scalar_one_or_none()

        if updated_link:
            # Update cache if the link was updated successfully
            cached_link = self.get_original_link_from_cache(short_code)
            if cached_link:
                logger.debug(f"Updating link in cache for short_code: {short_code}")
                cached_link.original_url = updated_link.original_url
                cached_link.expires_at = updated_link.expires_at
                cached_link.clicks = updated_link.clicks
                self.set_link_to_cache(short_code, cached_link)
            return updated_link
        else:
            logger.error(f"Failed to update link {short_code} in DB (maybe inactive?).")
            return None

    async def delete_link(self, short_code: str, delete_by: str) -> bool:
        """
        Delete a link by short_code (async). Returns True if deleted, False otherwise.
        """
        logger.debug(f"Attempting to delete link {short_code} by user: {delete_by}")

        link = await self.get_link_by_short_code(short_code)

        if not link:
            logger.warning(f"Link {short_code} not found for deletion.")
            return False

        # Permission check
        if link.created_by is not None and link.created_by != delete_by:
            logger.warning(
                f"User {delete_by} is not authorized to delete link {short_code} created by {link.created_by}."
            )
            raise PermissionError(f"User {delete_by} is not authorized to delete this link.")

        stmt = delete(Link).where(Link.short_code == short_code, Link.is_active == True)
        result = await self.session.execute(stmt)

        if result.rowcount > 0:
            logger.debug(f"Link {short_code} deleted successfully from DB.")
            self.redis_cache.delete(short_code)
            logger.debug(f"Link {short_code} deleted from cache.")
            return True
        else:
            logger.warning(f"Link {short_code} deletion affected 0 rows (maybe became inactive?).")
            return False

    async def record_click(self, short_code: str) -> None:
        """
        Record a click for a link (async): increment clicks, update last_used_at.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Link)
            .where(Link.short_code == short_code, Link.is_active == True)
            .values(clicks=Link.clicks + 1, last_used_at=now)
            .returning(Link.clicks, Link.last_used_at)
        )
        result = await self.session.execute(stmt)
        updated_values = result.fetchone()

        if updated_values:
            new_clicks, new_last_used_at = updated_values
            logger.debug(f"Recorded click for {short_code}. New clicks: {new_clicks}")
            # Update cache
            cached_link = self.get_original_link_from_cache(short_code)
            if cached_link:
                cached_link.clicks = new_clicks
                cached_link.last_used_at = new_last_used_at
                self.set_link_to_cache(short_code, cached_link)
                logger.debug(f"Cache updated for {short_code} after click.")
            else:
                logger.debug(f"Link {short_code} not in cache during click recording.")
        else:
            logger.warning(f"Failed to record click for non-existent or inactive link {short_code}")

    async def get_link_stats(self, short_code: str, get_by: str) -> dict | None:
        """
        Get link statistics (async). Requires owner permission.
        Returns a dictionary.
        """
        logger.debug(f"Fetching stats for link {short_code} requested by {get_by}")

        link_dict = await self.get_link(short_code)  # Uses cache/DB logic

        if not link_dict:
            logger.warning(f"Link stats request failed: Link {short_code} not found.")
            return None

        # Permission check
        if link_dict.get("created_by") is not None and link_dict["created_by"] != get_by:
            logger.warning(f"User {get_by} cannot get stats for link {short_code} owned by {link_dict['created_by']}.")
            raise PermissionError(f"User {get_by} is not authorized to get stats for this link.")

        return link_dict

    async def search_by_original_url(self, original_url: str) -> list[dict]:
        """
        Search active links by original URL (async). Returns list of dicts.
        """
        logger.debug(f"Searching active links with original_url: {original_url}")
        stmt = select(Link).where(Link.original_url == original_url, Link.is_active == True)
        result = await self.session.execute(stmt)
        links = result.scalars().all()

        return [
            {
                "short_code": link.short_code,
                "original_url": link.original_url,
                "created_at": link.created_at,
                "created_by": link.created_by,
                "clicks": link.clicks,
                "last_used_at": link.last_used_at,
                "expires_at": link.expires_at,
                "is_active": link.is_active,
                "updated_at": link.updated_at,
            }
            for link in links
        ]

    async def check_expired_links(self) -> list[str]:
        """
        Deactivate expired links (async). Returns list of deactivated short_codes.
        """
        logger.debug("Checking for expired links")
        now = datetime.now(timezone.utc)
        stmt = (
            update(Link)
            .where(
                Link.is_active == True,
                Link.expires_at.is_not(None),
                Link.expires_at < now,
            )
            .values(
                is_active=False,
                updated_at=now,
            )
            .returning(Link.short_code)
        )
        result = await self.session.execute(stmt)
        removed_short_codes = result.scalars().all()
        if removed_short_codes:
            logger.info(f"Deactivated expired links: {removed_short_codes}")
        return list(removed_short_codes)

    async def check_unused_links(self) -> list[str]:
        """
        Deactivate unused links based on threshold (async).
        Returns list of deactivated short_codes.
        """
        logger.debug("Checking for unused links")
        now = datetime.now(timezone.utc)
        threshold_time = now - timedelta(minutes=self.unused_cleanup_time)

        stmt = (
            update(Link)
            .where(
                Link.is_active == True,
                or_(
                    # Never used and created before threshold
                    (Link.last_used_at.is_(None) & (Link.created_at < threshold_time)),
                    # Last used before threshold
                    (Link.last_used_at.is_not(None) & (Link.last_used_at < threshold_time)),
                ),
            )
            .values(
                is_active=False,
                updated_at=now,
            )
            .returning(Link.short_code)
        )
        result = await self.session.execute(stmt)
        removed_short_codes = result.scalars().all()
        if removed_short_codes:
            logger.info(f"Deactivated unused links: {removed_short_codes}")
        return list(removed_short_codes)

    async def get_expired_links(self) -> list[dict]:
        """
        Get all inactive links (async). Returns list of dicts.
        """
        logger.debug("Fetching inactive (expired or unused) links")
        stmt = select(Link).where(Link.is_active == False)
        result = await self.session.execute(stmt)
        inactive_links = result.scalars().all()

        return [
            {
                "short_code": link.short_code,
                "original_url": link.original_url,
                "created_at": link.created_at,
                "created_by": link.created_by,
                "clicks": link.clicks,
                "last_used_at": link.last_used_at,
                "expires_at": link.expires_at,
                "is_active": link.is_active,
                "updated_at": link.updated_at,
            }
            for link in inactive_links
        ]

    def get_original_link_from_cache(self, short_code: str) -> LinkInDB | None:
        """Get link from Redis cache."""
        logger.info(f"Retrieving link from cache for short code: {short_code}")
        cached_link_json = self.redis_cache.get(short_code)

        if not cached_link_json:
            logger.debug(f"No link found in cache for short code: {short_code}")
            return None

        try:
            cached_link = LinkInDB.model_validate_json(cached_link_json)
            logger.info(f"Link found in cache for short code: {short_code}")
            return cached_link
        except Exception as e:
            logger.error(f"Failed to parse cached link {short_code} from JSON: {e}. Cache content: {cached_link_json}")
            return None

    def set_link_to_cache(self, short_code: str, link: LinkInDB) -> None:
        """Set link to Redis cache with appropriate TTL."""
        logger.info(f"Setting link to cache for short code: {short_code}")
        now_ts = datetime.now(timezone.utc).timestamp()
        if link.expires_at:
            expires_ts = link.expires_at.timestamp()
            ttl = int(expires_ts - now_ts)
            if ttl <= 0:
                logger.warning(
                    f"Link {short_code} expired (expires_at: {link.expires_at}). Removing from cache if exists."
                )
                self.redis_cache.delete(short_code)
                return
        else:
            ttl = get_settings().redis_settings.EXPIRES_IN_SECONDS

        try:
            link_json = link.model_dump_json()
            self.redis_cache.set(short_code, link_json, ex=ttl)
            logger.info(f"Link set to cache for {short_code} with TTL: {ttl} seconds")
        except Exception as e:
            logger.error(f"Failed to set link {short_code} to cache: {e}")


def get_links_repository(
    session: AsyncSession = Depends(get_async_db_session),
) -> LinksRepository:
    """FastAPI dependency provider for LinksRepository."""
    return LinksRepository(session=session)


# Background tasks now manage their own sessions
async def clean_up_expired_links():
    """Background task to deactivate expired links."""
    logger.info("Starting expired links cleanup task...")
    while True:
        session: AsyncSession | None = None
        try:
            async with async_session_factory() as session:
                links_repository = LinksRepository(session=session)
                redis_client = get_redis_client()
                logger.info("Running check for expired links...")
                removed_codes = await links_repository.check_expired_links()
                if removed_codes:
                    logger.info(f"Expired links deactivated: {removed_codes}. Removing from cache.")
                    for code in removed_codes:
                        redis_client.delete(code)
                else:
                    logger.info("No expired links found to deactivate.")
                await session.commit()
        except Exception as e:
            logger.error(f"Error during expired links cleanup: {e}", exc_info=True)

        interval = get_settings().links_service_settings.CLEANUP_LINKS_INTERVAL
        logger.info(f"Expired links cleanup check finished. Sleeping for {interval} seconds.")
        await asyncio.sleep(interval)


async def clean_up_unused_links():
    """Background task to deactivate unused links."""
    logger.info("Starting unused links cleanup task...")
    while True:
        session: AsyncSession | None = None
        try:
            async with async_session_factory() as session:
                links_repository = LinksRepository(session=session)
                redis_client = get_redis_client()
                logger.info("Running check for unused links...")
                removed_codes = await links_repository.check_unused_links()
                if removed_codes:
                    logger.info(f"Unused links deactivated: {removed_codes}. Removing from cache.")
                    for code in removed_codes:
                        redis_client.delete(code)
                else:
                    logger.info("No unused links found to deactivate.")
                await session.commit()
        except Exception as e:
            logger.error(f"Error during unused links cleanup: {e}", exc_info=True)

        interval = get_settings().links_service_settings.CLEANUP_LINKS_INTERVAL
        logger.info(f"Unused links cleanup check finished. Sleeping for {interval} seconds.")
        await asyncio.sleep(interval)
