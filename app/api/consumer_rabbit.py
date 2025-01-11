import json
import tempfile
from fastapi import FastAPI, BackgroundTasks
import aio_pika
import json
import os
import io
import asyncio

RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'audio_queue'
RESULT_QUEUE = 'result_queue_1'

async def start_consume():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
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
            original_format = data["original_format"]

            print(result_content)
            # # Убедитесь, что имя файла уникально, например, добавив идентификатор сообщения
            # filename = f"{data['message_id']}.{original_format}"
            # with open(filename, "wb") as f:
            #     f.write(audio_bytes)

        except Exception as e:
            await message.nack(requeue=False)

# async def receive_messages():
#     connection = aio_pika.connect_robust(RABBITMQ_HOST)
#     channel = await connection.channel()

#     # Ожидание объявления очереди, если она не существует
#     await channel.declare_queue(RESULT_QUEUE, durable=True)

#     async with channel.default_exchange() as exchange:
#         async for message in exchange.consume(RESULT_QUEUE, auto_ack=True):
#             # Обработка сообщения
#             data = json.loads(message.body.decode('utf-8'))
#             audio_bytes = bytes.fromhex(data["audio_bytes"])
#             original_format = data["original_format"]

#             # Убедитесь, что имя файла уникально, например, добавив идентификатор сообщения
#             filename = f"{data['message_id']}.{original_format}"
#             with open(filename, "wb") as f:
#                 f.write(audio_bytes)


    # await connection.close()

    