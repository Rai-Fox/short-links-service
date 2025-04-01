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
    ShortLinkAlreadyExistsException,
    LinkPermissionDeniedException,
)
from db.repositories.links import LinksRepository
from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)


class LinksService:
    def __init__(self, links_repository: LinksRepository):
        self.links_repository: LinksRepository = links_repository
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
        self,
        original_url: str,
        custom_alias: str | None,
        expires_at: datetime | None,
        created_by: str | None,
    ) -> LinkCreateResponse:
        if custom_alias:
            return await self.create_custom_short_code(
                original_url=original_url,
                custom_alias=custom_alias,
                expires_at=expires_at,
                created_by=created_by,
            )
        logger.info(f"Creating short link for: {original_url}")

        for attempt in range(self.generate_short_code_retries):
            short_code = await self._generate_short_code(original_url)
            existring_link = await self.links_repository.get_link(short_code)
            if existring_link:
                logger.warning(f"Short link {short_code} already exists. Retrying...")
                continue

            await self.links_repository.create_link(
                short_code=short_code,
                original_url=original_url,
                created_by=created_by,
                expires_at=expires_at,
            )
            logger.info(f"Short link created: {short_code}")
            return LinkCreateResponse(short_code=short_code, expires_at=expires_at)

        logger.error(f"Failed to create short link after {self.generate_short_code_retries} attempts.")
        raise ShortLinkAlreadyExistsException(detail="Failed to create short link after multiple attempts.")

    async def create_custom_short_code(
        self,
        original_url: str,
        custom_alias: str,
        expires_at: datetime | None,
        created_by: str | None,
    ) -> LinkCreateResponse:
        logger.info(f"Creating custom short link {custom_alias} for: {original_url}")
        short_code = custom_alias
        existing_link = await self.links_repository.get_link(short_code)

        if existing_link:
            logger.error(f"Custom short link {short_code} already exists.")
            raise ShortLinkAlreadyExistsException(detail=f"Custom short link {short_code} already exists.")

        await self.links_repository.create_link(
            short_code=short_code,
            original_url=original_url,
            created_by=created_by,
            expires_at=expires_at,
        )
        logger.info(f"Custom short link created: {short_code}")
        return LinkCreateResponse(short_code=short_code, expires_at=expires_at)

    async def get_original_link(self, short_code: str) -> RedirectResponse:
        logger.info(f"Retrieving original link for short URL: {short_code}")
        existing_link = await self.links_repository.get_link(short_code)
        if not existing_link:
            logger.error(f"Short link {short_code} not found.")
            raise ShortLinkNotFoundException(detail=f"Short link {short_code} not found.")
        await self.links_repository.record_click(short_code)
        original_url = existing_link["original_url"]
        logger.info(f"Redirecting to original URL: {original_url}")
        return RedirectResponse(url=original_url)

    async def update_link(
        self,
        short_code: str,
        new_original_url: str | None,
        new_expires_at: datetime | None,
        updated_by: str,
    ) -> None:
        logger.info(f"Updating link {short_code}")
        existing_link = await self.links_repository.get_link(short_code)

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
            logger.info(f"Link {short_code} updated successfully.")
        except PermissionError:
            logger.error(f"User {updated_by} is not authorized to update this link.")
            raise LinkPermissionDeniedException(detail=f"User {updated_by} is not authorized to update this link.")

    async def delete_link(self, short_code: str, delete_by: str) -> None:
        logger.info(f"Deleting link {short_code}")
        existing_link = await self.links_repository.get_link(short_code)
        if not existing_link:
            logger.error(f"Short link {short_code} not found.")
            raise ShortLinkNotFoundException(detail=f"Short link {short_code} not found.")

        try:
            await self.links_repository.delete_link(short_code=short_code, delete_by=delete_by)
            logger.info(f"Link {short_code} deleted successfully.")
        except PermissionError:
            logger.error(f"User {delete_by} is not authorized to delete this link.")
            raise LinkPermissionDeniedException(detail=f"User {delete_by} is not authorized to delete this link.")

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
