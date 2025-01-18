import io
import logging
import pika
import subprocess
import os
import json
import tempfile
from dotenv import load_dotenv

load_dotenv()

"""
Этот код когда тестил mq
RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'audio_queue'
RESULT_QUEUE = 'result_queue_1'
"""

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")
RESULT_QUEUE = os.getenv("RESULT_QUEUE")

logger = logging.getLogger(__name__)

def send_to_rabbitmq(audio_bytes, original_format, id_audio_users_requests):
    """
    Отправляет байткод аудио и формат файла в RabbitMQ
    """
    # connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    # channel = connection.channel()
    # channel.queue_declare(queue=RABBITMQ_QUEUE)
    # logger.info(f"НАЧАЛА СОЗДАНИЯ СООБЩЕНИИЯ")
    # # Формируем сообщение: байткод аудио + формат файла
    # message = {
    #     "audio_bytes": audio_bytes.hex(),  # Преобразуем байты в hex-строку для JSON
    #     "original_format": original_format
    # }
    # logger.info(f"message:{message}")
    # # Конвертируем сообщение в JSON и отправляем
    # channel.basic_publish(
    #     exchange='',
    #     routing_key=RABBITMQ_QUEUE,
    #     body=json.dumps(message).encode('utf-8'),
    #     # properties=pika.BasicProperties(
    #     #     delivery_mode=2,  # Сделать сообщение устойчивым
    #     # )
    # )
    # logger.info(f"СООБЩЕНИЕ ОТПРАВЛЕНО")
    # # connection.close()

    # connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    try:
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        logger.info(f"НАЧАЛА СОЗДАНИЯ СООБЩЕНИИЯ")

        message = {
            "audio_bytes": audio_bytes.hex(),  # Преобразуем байты в hex-строку для JSON
            "original_format": original_format,
            "id_audio_users_requests": id_audio_users_requests
        }
        logger.info(f"message:Обработка байтов")
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message).encode('utf-8'),
        )
        logger.info(f"СООБЩЕНИЕ ОТПРАВЛЕНО")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
    finally:
        if connection:
            connection.close()

def convert_to_audio(file: bytes, original_format: str) -> bytes:
    """
    Конвертирует файл в аудио формат (например, WAV) с помощью ffmpeg
    """
    # Создаем временный файл для входных данных
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{original_format}") as temp_input_file:
        temp_input_file.write(file)
        temp_input_path = temp_input_file.name

    # Создаем временный файл для выходных данных
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_output_file:
        temp_output_path = temp_output_file.name

    # Вызываем ffmpeg для конвертации
    subprocess.run([
        'ffmpeg', '-i', temp_input_path, '-f', 'wav', '-y', temp_output_path
    ], check=True)

    # Читаем байты из выходного файла
    with open(temp_output_path, 'rb') as output_file:
        audio_bytes = output_file.read()

    # Удаляем временные файлы
    os.remove(temp_input_path)
    os.remove(temp_output_path)

    return audio_bytes