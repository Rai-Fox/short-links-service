import traceback
from fastapi import APIRouter, Body, Depends, Path, Query, HTTPException
from fastapi.responses import RedirectResponse, Response
from authx.exceptions import MissingTokenError

from api.v1.schemas.links import (
    ExpiredLinksResponse,
    LinkCreate,
    LinkCreateResponse,
    LinkStats,
    LinkUpdate,
    LinkSearch,
    LinkSearchResponse,
    Link,
    LinkDelete,
)
from api.v1.services.links import LinksService
from api.v1.dependencies.links import get_links_service
from api.v1.exceptions.links import (
    LinkPermissionDeniedException,
    ShortLinkNotFoundException,
    InvalidShortLinkException,
    ShortLinkAlreadyExistsException,
)
from core.logging import get_logger
from api.v1.dependencies.auth import get_current_user, get_required_current_user
from core.security import TokenData

logger = get_logger(__name__)

links_router = APIRouter()


@links_router.get("/search", response_model=LinkSearchResponse)
async def search_links(
    original_link: str = Query(),
    links_service: LinksService = Depends(get_links_service),
):
    """
    Search for a short links by its original URL.
    """
    result = await links_service.search_link(original_url=original_link)
    return result


@links_router.get("/expired", response_model=ExpiredLinksResponse)
async def get_expired_links(
    links_service: LinksService = Depends(get_links_service),
):
    """
    Get all expired links.
    """
    expired_links = await links_service.get_expired_links()
    return expired_links


@links_router.post("/shorten")
async def shorten_link(
    short_code_create: LinkCreate = Body(...),
    links_service: LinksService = Depends(get_links_service),
    user: TokenData | None = Depends(get_current_user),
) -> LinkCreateResponse:
    """
    Shorten a given link.
    """
    try:
        short_code = await links_service.create_short_code(
            original_url=str(short_code_create.original_url),
            custom_alias=short_code_create.custom_alias,
            expires_at=short_code_create.expires_at,
            created_by=user.username if user else None,
        )
        return short_code
    except ShortLinkAlreadyExistsException:
        logger.error(f"Cannot shorten link {short_code_create.original_url}: Short link already exists.")
        raise


@links_router.get("/{short_code}/stats")
async def get_link_stats(
    short_code: str = Path(),
    links_service: LinksService = Depends(get_links_service),
    user: TokenData = Depends(get_required_current_user),
) -> LinkStats:
    """
    Get statistics for a given short link.
    """
    try:
        return await links_service.get_link_stats(short_code=short_code, get_by=user.username)
    except ShortLinkNotFoundException:
        logger.error(f"Short link {short_code} not found.")
        raise
    except PermissionError:
        logger.error(f"Permission denied for user {user.username} on short link {short_code}.")
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action. Please log in.",
        )


@links_router.get("/{short_code}")
async def get_short_code(
    short_code: str = Path(),
    links_service: LinksService = Depends(get_links_service),
) -> RedirectResponse:
    """
    Redirect to the original URL using the short link.
    """
    try:
        return await links_service.get_original_link(short_code)
    except ShortLinkNotFoundException:
        logger.error(f"Short link {short_code} not found.")
        raise


@links_router.put("/{short_code}")
async def update_link(
    link_data: LinkUpdate,
    short_code: str = Path(),
    links_service: LinksService = Depends(get_links_service),
    user: TokenData = Depends(get_required_current_user),
) -> Response:
    """
    Update a given short link.
    """

    try:
        await links_service.update_link(
            short_code=short_code,
            new_original_url=str(link_data.original_url),
            new_expires_at=link_data.expires_at,
            updated_by=user.username,
        )
        return Response(status_code=204)
    except ShortLinkNotFoundException:
        logger.error(f"Short link {short_code} not found.")
        raise
    except LinkPermissionDeniedException:
        logger.error(f"Permission denied for user {user.username} on short link {short_code}.")
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action. Please log in.",
        )


@links_router.delete("/{short_code}")
async def delete_link(
    short_code: str = Path(),
    links_service: LinksService = Depends(get_links_service),
    user: TokenData = Depends(get_required_current_user),
) -> Response:
    """
    Delete a given short link.
    """

    try:
        await links_service.delete_link(short_code=short_code, delete_by=user.username)
        return Response(status_code=204)
    except ShortLinkNotFoundException:
        logger.error(f"Short link {short_code} not found.")
        raise
    except LinkPermissionDeniedException:
        logger.error(f"Permission denied for user {user.username} on short link {short_code}.")
        raise HTTPException(
            status_code=403,
            detail="You are not authorized to perform this action. Please log in.",
        )
