
"""
Контроллер получает запросы от клиента, использует схемы для валидации данных, взаимодействует
с моделями для выполнения операций с базой данных и возвращает ответ клиенту/
"""

from fastapi import APIRouter, Depends, HTTPException, Request, FastAPI, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from schemas import UserResponse
from services import register_user
from auth import verify_access_token

from database import get_session
from schemas import UserResponse, UserRegistration
from models import User

from sqlmodel import Session
from bcrypt import hashpw, gensalt, checkpw


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/register")
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register_user(user: UserRegistration, session: Session = Depends(get_session)):
    hashed_password = hashpw(user.password.encode('utf-8'), gensalt())
    db_user = User(email=user.email, password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return user




# @router.post("/login", response_model=User1)
# async def login(user: UserLogin):
#     return await login_user(user)

@router.post("/admin/create_user")
async def create_user(user: UserRegistration, session: Session = Depends(get_session)):
    hashed_password = hashpw(user.password.encode('utf-8'), gensalt())
    db_user = User(email=user.email, password=hashed_password)
    print(db_user, hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return user

# @router.get("/me/", response_model=User)
# async def read_users_me(token_data: TokenData = Depends(verify_access_token)):
#     user = session.query(User).filter(User.email == token_data.email).first()
#     if user is None:
#         #todo raise пользователя нет
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# @router.get("/balance", response_model=Transaction)
# async def balance(current_user: User1 = Depends(get_current_user)):
#     return await get_balance(current_user)

# @router.post("/top_up", response_model=Transaction)
# async def top_up(amount: int, current_user: User1 = Depends(get_current_user)):
#     return await top_up_balance(current_user, amount)

# @router.post("/predict", response_model=PredictionResponse)
# async def predict(request: PredictionRequest, current_user: User1 = Depends(get_current_user)):
#     return await make_prediction(request, current_user)

# @router.get("/history", response_model=list[PredictionResponse])
# async def history(current_user: User1 = Depends(get_current_user)):
#     return await get_history(current_user)




import io
import pika
import subprocess
import os
import json
import tempfile

RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'audio_queue'
RESULT_QUEUE = 'result_queue'

def send_to_rabbitmq(audio_bytes, original_format):
    """
    Отправляет байткод аудио и формат файла в RabbitMQ
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    # Формируем сообщение: байткод аудио + формат файла
    message = {
        "audio_bytes": audio_bytes.hex(),  # Преобразуем байты в hex-строку для JSON
        "original_format": original_format
    }

    # Конвертируем сообщение в JSON и отправляем
    channel.basic_publish(
        exchange='',
        routing_key=RABBITMQ_QUEUE,
        body=json.dumps(message).encode('utf-8'),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Сделать сообщение устойчивым
        )
    )
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

@router.post("/upload_audio/")
async def upload_audio(file: UploadFile = File(...)):
    """
    Эндпоинт для загрузки файла и отправки аудио в RabbitMQ
    """
    # Проверяем, что файл был загружен
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не загружен")

    # Определяем формат файла по расширению
    original_format = file.filename.split('.')[-1].lower()

    # Читаем содержимое файла
    file_content = await file.read()

    # Конвертируем файл в аудио (например, WAV)
    audio_bytes = convert_to_audio(file_content, original_format)

    # Отправляем аудио и формат файла в RabbitMQ
    send_to_rabbitmq(audio_bytes, original_format)

    return {"message": "Файл успешно отправлен в RabbitMQ"}

