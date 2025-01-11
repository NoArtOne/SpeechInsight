
"""
Контроллер получает запросы от клиента, использует схемы для валидации данных, взаимодействует
с моделями для выполнения операций с базой данных и возвращает ответ клиенту
"""

from fastapi import APIRouter, Depends, HTTPException, Request, FastAPI, File, UploadFile
from rabbit_mq.producer_rabbit import convert_to_audio, send_to_rabbitmq

from database import get_session
from schemas import UserRegistration
from models import User

from sqlmodel import Session
from bcrypt import hashpw, gensalt, checkpw


router = APIRouter()

@router.post("/register")
async def register_user(user: UserRegistration, session: Session = Depends(get_session)):
    hashed_password = hashpw(user.password.encode('utf-8'), gensalt())
    db_user = User(email=user.email, password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return user

@router.post("/login", response_model=User1)
async def login(user: UserLogin):
    return await login_user(user)

# @app.post("/admin/create_user")
# async def create_user(user: UserRegistration, session: Session = Depends(get_session)):
#     hashed_password = hashpw(user.password.encode('utf-8'), gensalt())
#     db_user = User(email=user.email, password=hashed_password)
#     print(db_user, hashed_password)
#     session.add(db_user)
#     session.commit()
#     session.refresh(db_user)
#     return user

# @router.get("/balance", response_model=Transaction)
# async def balance(current_user: User1 = Depends(get_current_user)):
#     return await get_balance(current_user)

# @router.post("/top_up", response_model=Transaction)
# async def top_up(amount: int, current_user: User1 = Depends(get_current_user)):
#     return await top_up_balance(current_user, amount)

# @router.get("/history", response_model=list[PredictionResponse])
# async def history(current_user: User1 = Depends(get_current_user)):
#     return await get_history(current_user)

@router.post("/upload_audio/")
async def upload_audio(file: UploadFile = File(...)):
    """
    Эндпоинт для загрузки файла и отправки аудио в RabbitMQ
    """

    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не загружен")

    original_format = file.filename.split('.')[-1].lower()
    file_content = await file.read()
    audio_bytes = convert_to_audio(file_content, original_format)

    send_to_rabbitmq(audio_bytes, original_format)

    return {"message": "Файл успешно отправлен в RabbitMQ"}
