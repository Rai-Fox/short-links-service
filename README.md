# FastAPI Project

## Запуск проекта

```bash
docker-compose up --build
```

## Переменные окружения
Создайте файл `.env` и добавьте в него:

```
DATABASE_URL=postgresql+asyncpg://user:password@db/fastapi_db
SECRET_KEY=your_secret_key
```
