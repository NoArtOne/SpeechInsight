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

# async def check_rabbitmq_ready():
#     connection = None
#     while not connection:
#         try:
#             connection = await aio_pika.connect_robust(
#                 "amqp://{}:{}@{}:{}/".format(
#                     os.getenv("RABBITMQ_DEFAULT_USER"),
#                     os.getenv("RABBITMQ_DEFAULT_PASS"),
#                     "rabbitmq",
#                     "5672"
#                 )
#             )
#             print("RabbitMQ is ready")
#         except Exception as e:
#             print(f"RabbitMQ is not ready yet: {e}")
#             await asyncio.sleep(5)
#     await connection.close()

@app.on_event("startup")
async def startup_event():
    """
    Вызывается при старте сервера.
    - Инициализирует базу данных
    - Запускает RabbitMQ-консьюмер
    """
    # await check_rabbitmq_ready()
    init_db()
    asyncio.create_task(start_consume())    

if __name__ == "__main__":
    import uvicorn
    print("Запуск сервера FastAPI...")
    uvicorn.run(app, host="localhost", port=8000, reload=True)