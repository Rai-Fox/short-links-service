from datetime import datetime, timezone
import uuid

from fastapi import Depends
from fastapi.responses import RedirectResponse

from api.v1.schemas.links import (
    ExpiredLinksResponse,
    LinkCreate,
    LinkCreateResponse,
    LinkInDB,
    LinkStats,
    LinkUpdate,
    LinkSearch,
    LinkSearchResponse,
    Link,
    LinkDelete,
)
from api.v1.exceptions.links import (
    ShortLinkNotFoundException,
    InvalidShortLinkException,
    ShortLinkAlreadyExistsException,
    LinkPermissionDeniedException,
)
from db.repositories.links import LinksRepository
from core.config import get_settings
from core.redis import get_redis_client
from core.logging import get_logger

logger = get_logger(__name__)


class LinksService:
    def __init__(self, links_repository: LinksRepository):
        self.links_repository: LinksRepository = links_repository
        self.redis_cache = get_redis_client()
        self.generate_short_code_retries = get_settings().links_service_settings.GENERATE_SHORT_CODE_RETRIES
        self.short_code_length = get_settings().links_service_settings.SHORT_CODE_LENGTH

    async def _generate_short_code(self, original_url: str) -> str:
        """
        Generate a short link from the original URL.
        """
        short_code = str(uuid.uuid4())[: self.short_code_length]
        logger.debug(f"Generated short link: {short_code} for original URL: {original_url}")
        return short_code

    async def create_short_code(
        self, original_url: str, custom_alias: str | None, expires_at: datetime | None, created_by: str | None
    ) -> LinkCreateResponse:
        if custom_alias:
            return await self.create_custom_short_code(
                original_url=original_url, custom_alias=custom_alias, expires_at=expires_at, created_by=created_by
            )
        logger.info(f"Creating short link for: {original_url}")

        for attempt in range(self.generate_short_code_retries):
            short_code = await self._generate_short_code(original_url)
            if short_code == "search" or short_code == "expired":
                logger.error(f"Generated short code {short_code} is invalid. Retrying...")
                continue
            existring_link = await self.links_repository.get_link(short_code)
            if existring_link:
                logger.warning(f"Short link {short_code} already exists. Retrying...")
                continue
            try:
                await self.links_repository.create_link(
                    short_code=short_code,
                    original_url=original_url,
                    created_by=created_by,
                    expires_at=expires_at,
                )
                logger.info(f"Short link created: {short_code}")
                return LinkCreateResponse(short_code=short_code, expires_at=expires_at)
            except ShortLinkAlreadyExistsException:
                logger.warning(
                    f"Short link {short_code} already exists."
                    f"Retrying... (attempt {attempt + 1}/{self.generate_short_code_retries})"
                )

        logger.error(f"Failed to create short link after {self.generate_short_code_retries} attempts.")
        raise ShortLinkAlreadyExistsException(detail="Failed to create short link after multiple attempts.")

    async def create_custom_short_code(
        self, original_url: str, custom_alias: str, expires_at: datetime | None, created_by: str | None
    ) -> LinkCreateResponse:
        logger.info(f"Creating custom short link {custom_alias} for: {original_url}")
        short_code = custom_alias
        existing_link = await self.links_repository.get_link(short_code)

        if existing_link:
            logger.error(f"Custom short link {short_code} already exists.")
            raise ShortLinkAlreadyExistsException(detail=f"Custom short link {short_code} already exists.")

        try:
            await self.links_repository.create_link(
                short_code=short_code,
                original_url=original_url,
                created_by=created_by,
                expires_at=expires_at,
            )
            logger.info(f"Custom short link created: {short_code}")
            return LinkCreateResponse(short_code=short_code, expires_at=expires_at)
        except ShortLinkAlreadyExistsException:
            logger.error(f"Custom short link {short_code} already exists.")
            raise ShortLinkAlreadyExistsException(detail=f"Custom short link {short_code} already exists.")

    async def get_original_link(self, short_code: str) -> RedirectResponse:
        logger.info(f"Retrieving original link for short URL: {short_code}")
        existing_link = await self.links_repository.get_link(short_code)
        if not existing_link:
            logger.error(f"Short link {short_code} not found.")
            raise ShortLinkNotFoundException(detail=f"Short link {short_code} not found.")
        await self.links_repository.record_click(short_code)
        original_url = existing_link["original_url"]
        logger.info(f"Redirecting to original URL: {original_url}")
        # Set the link to cache
        self.set_link_to_cache(short_code, LinkInDB(**existing_link))
        return RedirectResponse(url=original_url)

    async def update_link(
        self,
        short_code: str,
        new_original_url: str | None,
        new_expires_at: datetime | None,
        updated_by: str,
    ) -> None:
        logger.info(f"Updating link {short_code}")
        existing_link = await self.links_repository.get_link(short_code=short_code)

        if not existing_link:
            logger.error(f"Short link {short_code} not found.")
            raise ShortLinkNotFoundException(detail=f"Short link {short_code} not found.")

        try:
            await self.links_repository.update_link(
                short_code=short_code,
                new_original_url=new_original_url,
                new_expires_at=new_expires_at,
                updated_by=updated_by,
            )

            # Update the link in cache
            if new_original_url:
                existing_link["original_url"] = new_original_url
            if new_expires_at:
                existing_link["expires_at"] = new_expires_at
            self.set_link_to_cache(short_code, LinkInDB(**existing_link))

            logger.info(f"Link {short_code} updated successfully.")
        except PermissionError:
            logger.error(f"User {updated_by} is not authorized to update this link.")
            raise LinkPermissionDeniedException(detail=f"User {updated_by} is not authorized to update this link.")
        except ValueError:
            logger.error(f"Link {short_code} not found.")
            raise ShortLinkNotFoundException(detail=f"Short link {short_code} not found.")

    async def delete_link(self, short_code: str, delete_by: str) -> None:
        logger.info(f"Deleting link {short_code}")
        existing_link = await self.links_repository.get_link(short_code)
        if not existing_link:
            logger.error(f"Short link {short_code} not found.")
            raise ShortLinkNotFoundException(detail=f"Short link {short_code} not found.")

        try:
            await self.links_repository.delete_link(short_code=short_code, delete_by=delete_by)

            # Remove the link from cache
            self.redis_cache.delete(short_code)

            logger.info(f"Link {short_code} deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete link {short_code}: {str(e)}")
            raise ShortLinkNotFoundException(detail=f"Failed to delete short link {short_code}.")

    async def get_link_stats(self, short_code: str, get_by: str) -> LinkStats:
        logger.info(f"Retrieving stats for short link {short_code}")
        link_stats = await self.links_repository.get_link_stats(short_code=short_code, get_by=get_by)
        if not link_stats:
            logger.error(f"Link stats for {short_code} not found.")
            raise ShortLinkNotFoundException(detail=f"Link stats for {short_code} not found.")

        return LinkStats(**link_stats)

    async def search_link(self, original_url: str) -> LinkSearchResponse:
        logger.info(f"Searching for link with original URL: {original_url}")
        links = await self.links_repository.search_by_original_url(original_url=original_url)
        if not links:
            logger.warning(f"No link found for original URL: {original_url}")
            return LinkSearchResponse(original_url=original_url, links=[])
        return LinkSearchResponse(original_url=original_url, links=[Link(**link) for link in links])

    async def get_expired_links(self) -> ExpiredLinksResponse:
        logger.info(f"Retrieving expired links")
        expired_links = await self.links_repository.get_expired_links()
        if not expired_links:
            logger.warning(f"No expired links found.")
            return ExpiredLinksResponse(expired_links=[])

        return ExpiredLinksResponse(expired_links=[Link(**link) for link in expired_links])

    def get_original_link_from_cache(self, short_code: str) -> LinkInDB | None:
        """
        Get a link from the cache.
        """
        logger.info(f"Retrieving link from cache for short code: {short_code}")
        cached_link = self.redis_cache.get(short_code)

        if not cached_link:
            logger.warning(f"No link found in cache for short code: {short_code}")
            return None

        logger.info(f"Link found in cache for short code: {short_code}")

        if isinstance(cached_link, str):
            cached_link = LinkInDB.model_validate_json(cached_link)
            return cached_link

        return LinkInDB(**cached_link)

    def set_link_to_cache(self, short_code: str, link: LinkInDB) -> None:
        """
        Set a link to the cache.
        """
        logger.info(f"Setting link to cache for short code: {short_code}")
        if not link.expires_at:
            expires = get_settings().redis_settings.EXPIRES_IN_SECONDS
        else:
            expires = link.expires_at.timestamp() - datetime.now(timezone.utc).timestamp()
        if expires <= 0:
            logger.warning(f"Link {short_code} has already expired. Not setting to cache.")
            return
        self.redis_cache.set(short_code, link.model_dump_json(), ex=expires)
        logger.info(f"Link set to cache for short code: {short_code}")
