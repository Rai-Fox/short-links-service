import traceback
from fastapi import Depends, APIRouter, HTTPException

from api.v1.schemas.auth import (
    UserLogin,
    UserRegister,
)
from api.v1.services.auth import AuthService
from api.v1.exceptions.auth import InvalidCredentialsException, UserNotFoundException, UserAlreadyExistsException
from api.v1.dependencies.auth import get_auth_service
from core.logging import get_logger
from core.security import Token

logger = get_logger(__name__)


auth_router = APIRouter()


@auth_router.post("/register", response_model=Token)
async def register_user(credentials: UserRegister, auth_service: AuthService = Depends(get_auth_service)):
    try:
        return await auth_service.register_user(credentials)
    except UserAlreadyExistsException:
        logger.error(f"Cannot register user {credentials.username}: User already exists.")
        raise
    except InvalidCredentialsException:
        logger.error(f"Cannot register user {credentials.username}: Invalid credentials.")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during registration for user {credentials.username}: {str(e)} {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@auth_router.post("/login", response_model=Token)
async def login_user(credentials: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    try:
        return await auth_service.login_user(credentials)
    except InvalidCredentialsException:
        logger.error(f"Cannot login user {credentials.username}: Invalid credentials.")
        raise
    except UserNotFoundException:
        logger.error(f"Cannot login user {credentials.username}: User not found.")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login for user {credentials.username}: {str(e)} {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")
