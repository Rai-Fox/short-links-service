from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
import uvicorn

from core.config import get_settings


app = FastAPI(
    title=get_settings().app_setings.NAME,
    description=get_settings().app_setings.DESCRIPTION,
    version=get_settings().app_setings.VERSION,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
)


class StatusResponse(BaseModel):
    status: str

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "App healthy"}]})


@app.get("/", response_model=StatusResponse)
async def health_check():
    return StatusResponse(status="App healthy")


if __name__ == "__main__":
    uvicorn.run(app, host=get_settings().fastapi_settings.HOST, port=get_settings().fastapi_settings.PORT)
