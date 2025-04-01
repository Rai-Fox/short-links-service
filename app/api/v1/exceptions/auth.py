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
