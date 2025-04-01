# 🔗 Short Links Service

🚀 Высокопроизводительное и расширяемое API-сервис для генерации и управления короткими ссылками, основанное на FastAPI.

## 🔧 Возможности

- Генерация коротких ссылок
- Авторизация пользователей через JWT
- Очистка устаревших и неиспользуемых ссылок
- Swagger-документация: `/api/openapi`
- Асинхронная архитектура
- Docker-контейнеризация

## 💡 Используемые технологии

- FastAPI
- Uvicorn
- PostgreSQL
- Redis
- AuthX (JWT-аутентификация)
- Docker & Docker Compose
- pytest (тестирование)
- SQLAlchemy (ORM)
- Pydantic (валидация данных)

---

## 📂 Установка и запуск

### Через Docker:
```bash
git clone https://github.com/Rai-Fox/short-links-service.git
cd short-links-service
docker-compose up --build -d
```

---

## 📁 Структура проекта

```
.
├── app/                # Исходный код
│   ├── api/            # Эндпоинты, зависимости, сервисы и схемы
│   ├── core/           # Конфигурации и логирование
│   ├── db/             # Работа с базой данных
│   └── main.py         # Точка входа
├── tests/              # Тесты
├── htmlcov/            # Отчёты покрытия
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔌 API эндпоинты

### `POST /v1/links/shorten`
Создание новой короткой ссылки.

**JSON:**
```json
{
  "original_url": "https://example.com",
  "custom_alias": "example123",           // optional
  "expires_at": "2025-03-01 00:24:13Z"    // optional
}
```


### `GET /v1/links/search?original_link=...`
Поиск короткой ссылки по оригинальному URL.

### `GET /v1/links/expired`
Получение всех просроченных ссылок.


### `PUT /v1/links/{short}`
Обновление информации по ссылке.

### `GET /v1/links/{short}`
Редирект по короткой ссылке (307).

### `GET /v1/links/{short}/stats`
Получение статистики переходов.

### `DELETE /v1/links/{short}`
Удаление ссылки.

---

## 📄 Конфигурация через .env и docker-compose.yml

| Переменная | Назначение | Пример |
|------------|------------|--------|
| `APP_NAME` | Название | `"Short Links Service"` |
| `FASTAPI_HOST` | Хост API | `0.0.0.0` |
| `FASTAPI_PORT` | Порт | `8000` |
| `DATABASE_HOST` | Хост БД | `db` |
| `DATABASE_PORT` | Порт БД | `5432` |
| `DATABASE_NAME` | Имя БД | `links_db` |
| `DATABASE_USER` | Секрет-файл пользователя | `/run/secrets/db_user` |
| `DATABASE_PASSWORD` | Секрет-файл пароля | `/run/secrets/db_password` |
| `REDIS_HOST` | Хост Redis | `redis` |
| `REDIS_PORT` | Порт Redis | `6379` |
| `JWT_SECRET_KEY` | Ключ подписи | `/run/secrets/jwt_secret_key` |
| `JWT_ALGORITHM` | Алгоритм подписи | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | TTL токена | `5` |
| `LINKS_SERVICE_UNUSED_LINKS_THRESHOLD` | Порог "заброшенности" | `120` |

И другие переменные, которые можно настроить в `docker-compose.yml` или `.env` файле.
---

## 📊 База данных и кеш

### PostgreSQL
Используется для хранения пользователей, ссылок, информации о переходах и статистики.
- Таблица `links` для хранения ссылок.
- Таблица `users` для хранения пользователей.

### Redis
Используется для ускорения редиректов и хранения TTL.

---

## 🔒 Авторизация
JWT через библиотеку `authx`. Для защищённых эндпоинтов требуется заголовок:
```
Authorization: Bearer <token>
```

---

## 🪥 Очистка данных

При старте сервис автоматически:
- Удаляет просроченные ссылки (`expires_at < now()`)
- Удаляет заброшенные ссылки (без переходов за `LINKS_SERVICE_UNUSED_LINKS_THRESHOLD` секунд)

---

## 🧪 Тестирование
```bash
pytest
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 📅 Лицензия
MIT License

---

© Сергей Бородачев, 2025

