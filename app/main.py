import asyncio
import logging
import os
import aio_pika
from fastapi import FastAPI
from api.controller import router
from database import init_db
from rabbit_mq.consumer_rabbit import start_consume

app = FastAPI()

app.include_router(router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    uvicorn.run(app, host="localhost", port=8000, reload=True)