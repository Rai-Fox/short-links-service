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
mkdir app/schemas
mkdir app/services
mkdir app/tests
mkdir app/tests/api
mkdir app/tests/db
mkdir app/tests/services
mkdir migrations
mkdir scripts

# Файлы с начальными шаблонами

# app/main.py
cat <<EOL > app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
EOL

# app/core/config.py
cat <<EOL > app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
EOL

# app/core/security.py
cat <<EOL > app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
EOL

# Dockerfile
cat <<EOL > Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOL

# docker-compose.yml
cat <<EOL > docker-compose.yml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: fastapi_db
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
EOL

# requirements.txt
cat <<EOL > requirements.txt
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
cat <<EOL > README.md
# FastAPI Project

## Запуск проекта

\`\`\`bash
docker-compose up --build
\`\`\`

## Переменные окружения
Создайте файл \`.env\` и добавьте в него:

\`\`\`
DATABASE_URL=postgresql+asyncpg://user:password@db/fastapi_db
SECRET_KEY=your_secret_key
\`\`\`
EOL

# Оставшиеся файлы
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/api/v1/schemas/__init__.py
touch app/api/v1/services/__init__.py
touch app/api/v1/dependencies/__init__.py
touch app/tests/__init__.py
touch app/tests/api/__init__.py
touch app/tests/db/__init__.py
touch app/tests/services/__init__.py
touch app/core/__init__.py
touch app/core/utils.py
touch app/db/base.py
touch app/db/models/__init__.py
touch app/db/repositories/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch .env .gitignore

# Done
echo "Структура проекта FastAPI успешно создана!"
