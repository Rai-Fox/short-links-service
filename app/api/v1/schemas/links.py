from datetime import datetime, timezone
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field, field_validator


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = None
    expires_at: datetime | None = None

    @field_validator("expires_at")
    def check_expires_at(cls, value):
        if value and value < datetime.now(timezone.utc):
            raise ValueError("expires_at must be a future datetime")
        return value

    @field_validator("custom_alias")
    def check_custom_alias(cls, value):
        if not value:
            return value

        if not value.isalnum():
            raise ValueError("custom_alias must be alphanumeric")
        if len(value) < 3 or len(value) > 20:
            raise ValueError("custom_alias must be between 3 and 20 characters")
        if value.lower() == "search":
            raise ValueError("custom_alias cannot be 'search'")
        if value.lower() == "expired":
            raise ValueError("custom_alias cannot be 'expired'")

        return value


class LinkCreateResponse(BaseModel):
    """
    Model for the response of a link creation.
    It includes the original URL and the short URL.
    """

    short_code: str
    expires_at: datetime | None = None


class LinkGet(BaseModel):
    """
    Model for retrieving a link.
    It includes the short URL.
    """

    short_code: str


class LinkStats(BaseModel):
    original_url: HttpUrl
    created_at: datetime
    clicks: int = Field(ge=0)
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    short_code: str


class LinkUpdate(BaseModel):
    """
    Model for updating a link.
    It allows updating the original_url, or expiration time.
    """

    original_url: HttpUrl | None = None
    expires_at: datetime | None = None

    @field_validator("expires_at")
    def check_expires_at(cls, value):
        if value and value < datetime.now():
            raise ValueError("expires_at must be a future datetime")
        return value


class LinkDelete(BaseModel):
    """
    Model for deleting a link.
    It includes the short URL to be deleted.
    """

    short_code: str


class LinkSearch(BaseModel):
    """
    Model for searching a link by its original URL.
    """

    original_url: HttpUrl


class Link(BaseModel):
    """
    Model for an expired link.
    """

    original_url: HttpUrl
    short_code: str
    expires_at: datetime | None
    created_at: datetime
    clicks: int = Field(ge=0)
    last_used_at: datetime | None = None
    created_by: str | None


class LinkSearchResponse(BaseModel):
    """
    Model for the response of a link search.
    It includes the original URL and the short URL.
    """

    original_url: HttpUrl
    links: list[Link] = Field(default_factory=list)


class ExpiredLinksResponse(BaseModel):
    """
    Model for the response of expired links.
    It includes the original URL, short URL, and expiration time.
    """

    expired_links: list[Link] = Field(default_factory=list)


class LinkInDB(BaseModel):
    """
    Model for a link in the database.
    It includes the original URL, short URL, and expiration time.
    """

    short_code: str
    original_url: HttpUrl
    created_at: datetime
    created_by: str | None = None
    clicks: int = Field(ge=0)
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
