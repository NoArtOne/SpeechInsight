FROM python:3.13-slim

WORKDIR /app

# Установка необходимых системных пакетов
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Установка зависимостей Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Копирование остального кода в контейнер
COPY . .

# Экспозиция порта, на котором будет работать приложение
EXPOSE 8000

# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
