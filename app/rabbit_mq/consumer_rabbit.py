import json
import logging
import select

from fastapi import Depends
from sqlmodel import Session, select
# from sqlalchemy.orm import Session
import aio_pika
import json
import asyncio
import os
from database import get_session
from models import RequestAudio
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")
RESULT_QUEUE = os.getenv("RESULT_QUEUE")
RABBITMQ_PORT=os.getenv("RABBITMQ_PORT") 
RABBITMQ_USER=os.getenv("RABBITMQ_USER") 
RABBITMQ_PASS=os.getenv("RABBITMQ_PASS")
print(f"RABBITMQ_HOST: {RABBITMQ_HOST}, RABBITMQ_QUEUE:{RABBITMQ_QUEUE}, RESULT_QUEUE:{RESULT_QUEUE}")

async def start_consume():
    # connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    connection1 = await aio_pika.connect_robust(f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/")
    async with connection1:
        channel = await connection1.channel()
        queue = await channel.declare_queue(RESULT_QUEUE)
        await queue.consume(callback)
        await asyncio.Future()  # Run forever

async def callback(message: aio_pika.IncomingMessage):
    try:
        # Обработка сообщения
        logger.info(f"message.body: {message.body}")
        logger.info(f"message.body.decode('utf-8'): {message.body.decode('utf-8')}")
        data = json.loads(message.body.decode('utf-8'))
        logger.info(f"data: {data}")
        result_content = data["result_content"]
        id_audio_users_requests = data["id_audio_users_requests"]
        logger.info(f"result_content: {result_content}")
        
        logger.info(f"result_content: {result_content}")
        session_generator = get_session()
        session = next(session_generator)
        db_request = session.exec(select(RequestAudio).where(RequestAudio.id == id_audio_users_requests)).first()
        if db_request:
            db_request.output_text = result_content
            session.commit()
        else:
            logger.warning(f"Неверный id requests")
        
        # Явное подтверждение успешной обработки
        await message.ack()
        
    except Exception as e:
        # В случае ошибки отклоняем сообщение
        logger.info(f"Error processing message: {e}")
        await message.reject(requeue=False)
    