import asyncio
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
import uvicorn

from core.config import get_settings
from api.v1 import links_router, auth_router
from db import create_tables, drop_tables
from db.repositories.links import clean_up_unused_links, clean_up_expired_links


@asynccontextmanager
async def lifespan(app):
    await drop_tables()
    await create_tables()
    # Cron job to clean up expired links
    asyncio.create_task(clean_up_expired_links())
    asyncio.create_task(clean_up_unused_links())

    yield


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
    """
    Global exception handler for the application.
    For debugging purposes only.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "tb": traceback.format_exc()},
    )


if __name__ == "__main__":
    uvicorn.run(app, host=get_settings().fastapi_settings.HOST, port=get_settings().fastapi_settings.PORT)
