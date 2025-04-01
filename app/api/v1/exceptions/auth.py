from fastapi import HTTPException


class UserAlreadyExistsException(HTTPException):
    """Exception raised when a user already exists."""

    def __init__(self, detail="User already exists."):
        super().__init__(status_code=400, detail=detail)


class InvalidCredentialsException(HTTPException):
    """Exception raised for invalid credentials."""

    def __init__(self, detail="Invalid credentials."):
        super().__init__(status_code=401, detail=detail)


class UserNotFoundException(HTTPException):
    """Exception raised when a user is not found."""

    def __init__(self, detail="User not found."):
        super().__init__(status_code=404, detail=detail)


class ExpiredTokenException(HTTPException):
    """Exception raised when a token has expired."""

    def __init__(self, detail="Token has expired."):
        super().__init__(status_code=401, detail=detail)


class MissingTokenException(HTTPException):
    """Exception raised when a token is missing."""

    def __init__(self, detail="Missing token."):
        super().__init__(status_code=401, detail=detail)


class InvalidTokenException(HTTPException):
    """Exception raised for invalid token."""

    def __init__(self, detail="Invalid token."):
        super().__init__(status_code=401, detail=detail)
