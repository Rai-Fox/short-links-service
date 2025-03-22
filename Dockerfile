FROM python:3.11-slim


WORKDIR /app

# Установим системные зависимости для PostgreSQL и сборки Python-зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app/main.py"]