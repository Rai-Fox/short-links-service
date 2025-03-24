from fastapi import HTTPException


class ShortLinkNotFoundException(HTTPException):
    """Exception raised when a short link is not found."""

    def __init__(self, detail="Short link not found."):
        super().__init__(status_code=404, detail=detail)


class InvalidShortLinkException(HTTPException):
    """Exception raised for invalid short link format."""

    def __init__(self, detail="Invalid short link format."):
        super().__init__(status_code=400, detail=detail)


class ShortLinkAlreadyExistsException(HTTPException):
    """Exception raised when a short link already exists."""

    def __init__(self, detail="Short link already exists."):
        super().__init__(status_code=400, detail=detail)


class LinkPermissionDeniedException(HTTPException):
    """Exception raised when a user does not have permission to update a link."""

    def __init__(self, detail="You do not have permission to update this link."):
        super().__init__(status_code=403, detail=detail)
