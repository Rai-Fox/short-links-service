#!/bin/bash

# Создание базовой структуры проекта FastAPI в текущей папке

# Папки
mkdir app
mkdir app/api
mkdir app/api/v1
mkdir app/api/v1/endpoints
mkdir app/api/v1/schemas
mkdir app/api/v1/services
mkdir app/api/v1/dependencies
mkdir app/core
mkdir app/db
mkdir app/db/models
mkdir app/db/repositories
mkdir tests
mkdir tests/api
mkdir tests/db
mkdir tests/services
mkdir migrations
mkdir scripts
mkdir secrets

# Файлы с начальными шаблонами

# app/main.py
cat <<EOL >app/main.py
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
EOL

# app/core/config.py
cat <<EOL >app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
EOL

# app/core/logging.py
cat <<EOL >app/core/logging.py
import logging
import logging.config


logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "myapp": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}


def get_logger(name: str) -> logging.Logger:
    logging.config.dictConfig(logging_config)
    return logging.getLogger(name)
EOL

# Dockerfile
cat <<EOL >Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOL

# docker-compose.yml
cat <<EOL >docker-compose.yml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - FASTAPI_HOST=0.0.0.0
      - FASTAPI_PORT=8000
      - APP_NAME="App Name"
      - APP_VERSION=1.0.0
      - APP_DESCRIPTION="App Description"
      - DATABASE_HOST=db
      - DATABASE_PORT=5432
      - DATABASE_USER=/run/secrets/db_user
      - DATABASE_PASSWORD=/run/secrets/db_password
      - DATABASE_NAME=links_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - JWT_SECRET_KEY=/run/secrets/jwt_secret_key
    secrets:
       - db_user
       - db_password
       - jwt_secret_key
    depends_on:
      - db
      - redis
    networks:
      - app_network

  db:
    image: postgres:15-alpine
    container_name: db
    environment:
      POSTGRES_USER: /run/secrets/db_user
      POSTGRES_PASSWORD: /run/secrets/db_password
      DATABASE_NAME: links_db
      POSTGRES_DB: fastapi_db
    secrets:
       - db_user
       - db_password
    ports:
      - "5432:5432"
    networks:
      - app_network

  redis:
    image: redis:7-alpine
    container_name: redis
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
    ports:
      - "6379:6379"
    networks:
      - app_network


networks:
  app_network:
    driver: bridge


secrets:
  db_password:
    file: ./secrets/db_password.txt
  db_user:
    file: ./secrets/db_user.txt
  jwt_secret_key:
    file: ./secrets/jwt_secret_key.txt
EOL

# requirements.txt
cat <<EOL >requirements.txt
fastapi
uvicorn[standard]
sqlalchemy
alembic
asyncpg
pydantic-settings
passlib[bcrypt]
python-jose
redis
EOL

# README.md
cat <<EOL >README.md
# FastAPI Project

## Запуск проекта

\`\`\`bash
docker-compose up --build -d
\`\`\`

## Секреты
Секреты хранятся в папке \`secrets\`. Не забудьте создать файлы \`db_user.txt\`, \`db_password.txt\` и \`jwt_secret_key.txt\` с соответствующими значениями.
EOL

# .dockerignore
cat <<EOL >.dockerignore
secrets/
.env
*.pyc
__pycache__/
.git
.gitignore
README.md
docker-compose.yml
Dockerfile
LICENSE
EOL

# Оставшиеся файлы
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/api/v1/schemas/__init__.py
touch app/api/v1/services/__init__.py
touch app/api/v1/dependencies/__init__.py
touch app/core/__init__.py
touch app/core/utils.py
touch app/core/logging.py
touch app/db/__init__.py
touch app/db/base.py
touch app/db/models/__init__.py
touch app/db/repositories/__init__.py

touch tests/__init__.py
touch tests/api/__init__.py
touch tests/db/__init__.py
touch tests/services/__init__.py

touch secrets/db_user.txt
touch secrets/db_password.txt
touch secrets/jwt_secret_key.txt
touch secrets/.gitkeep

touch .env .gitignore

# Done
echo "Структура проекта FastAPI успешно создана!"
