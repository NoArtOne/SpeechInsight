import asyncio
from fastapi import FastAPI
from api.controller import router
from database import init_db
from rabbit_mq.consumer_rabbit import start_consume

app = FastAPI()

# Подключаем роутеры
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """
    Вызывается при старте сервера.
    - Инициализирует базу данных
    - Запускает RabbitMQ-консьюмер
    """
    init_db()
    asyncio.create_task(start_consume())

if __name__ == "__main__":
    import uvicorn
    print("Запуск сервера FastAPI...")
    uvicorn.run(app, host="localhost", port=8000)