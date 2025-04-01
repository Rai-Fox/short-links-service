import asyncio
import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging  # Импортируем logging для uvicorn

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import uvicorn
from authx.exceptions import AuthXException

from core.config import get_settings
from core.logging import LOGGING_CONFIG, get_logger
from api.v1 import links_router, auth_router
from db import create_tables, drop_tables
from db.repositories.links import clean_up_unused_links, clean_up_expired_links

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events: startup and shutdown."""
    logger.info("Application lifespan starting...")

    # await drop_tables()
    logger.info("Creating database tables...")
    await create_tables()
    logger.info("Database tables creation finished.")

    logger.info("Starting background link cleanup tasks...")
    expired_cleanup_task = asyncio.create_task(clean_up_expired_links())
    unused_cleanup_task = asyncio.create_task(clean_up_unused_links())
    logger.info("Background tasks started.")

    yield

    logger.info("Application lifespan ending...")
    logger.info("Cancelling background tasks...")
    expired_cleanup_task.cancel()
    unused_cleanup_task.cancel()
    try:
        await asyncio.gather(expired_cleanup_task, unused_cleanup_task, return_exceptions=True)
        logger.info("Background tasks cancelled.")
    except asyncio.CancelledError:
        logger.info("Background tasks cancellation processed.")

    logger.info("Application shutdown complete.")


app = FastAPI(
    title=get_settings().app_setings.NAME,
    description=get_settings().app_setings.DESCRIPTION,
    version=get_settings().app_setings.VERSION,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.include_router(links_router, prefix="/v1/links", tags=["links"])
app.include_router(auth_router, prefix="/v1/auth", tags=["auth"])


class StatusResponse(BaseModel):
    status: str
    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "App healthy"}]})


@app.get("/", response_model=StatusResponse)
async def health_check():
    return StatusResponse(status="App healthy")


@app.exception_handler(Exception)
async def base_exception_handler(request: Request, exc: Exception):
    """Global handler for unexpected exceptions. Logs the error and returns 500."""
    logger.error(f"Unhandled exception during request {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


@app.exception_handler(AuthXException)
async def authx_exception_handler(request: Request, exc: AuthXException):
    """Handler for AuthX authentication/authorization errors."""
    logger.warning(f"AuthX exception for {request.url.path}: {exc.detail} (Status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),  # Include headers like WWW-Authenticate if present
    )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=get_settings().fastapi_settings.HOST,
        port=get_settings().fastapi_settings.PORT,
        log_level=logging.DEBUG,
        log_config=LOGGING_CONFIG,
    )
