import json
import aio_pika
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.getenv("RESULT_QUEUE")
RESULT_QUEUE = os.getenv("RESULT_QUEUE")
RABBITMQ_PORT=os.getenv("RABBITMQ_PORT") 
RABBITMQ_USER=os.getenv("RABBITMQ_USER") 
RABBITMQ_PASS=os.getenv("RABBITMQ_PASS")
print(f"RABBITMQ_HOST: {RABBITMQ_HOST}, RABBITMQ_QUEUE:{RABBITMQ_QUEUE}, RESULT_QUEUE:{RESULT_QUEUE}")

"""
# RABBITMQ_HOST = 'localhost'
# RABBITMQ_QUEUE = 'audio_queue'
# RESULT_QUEUE = 'result_queue_1'
Это было когда тестил rabbit_mq
"""

async def start_consume():
    # connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    connection = await aio_pika.connect_robust(f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/")
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(RESULT_QUEUE)
        await queue.consume(callback)
        await asyncio.Future()  # Run forever

async def callback(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            # Обработка сообщения
            data = json.loads(message.body.decode('utf-8'))
            result_content = data["result_content"]

            print(result_content)
            #todo BD

            # # Убедитесь, что имя файла уникально, например, добавив идентификатор сообщения
            # filename = f"{data['message_id']}.{original_format}"
            # with open(filename, "wb") as f:
            #     f.write(audio_bytes)

        except Exception as e:
            await message.nack(requeue=False)


    