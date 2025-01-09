# Используем официальный образ Python 3.12.3
FROM python:3.12.3-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл requirements.txt в контейнер
COPY requirements.txt requirements.txt

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем остальные файлы проекта в контейнер
COPY . .

# Копируем модель Whisper в контейнер
COPY whisper /app/whisper

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
