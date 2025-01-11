"""
Контроллер получает запросы от клиента, использует схемы для валидации данных, взаимодействует
с моделями для выполнения операций с базой данных и возвращает ответ клиенту
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, FastAPI, File, UploadFile
from pydantic import EmailStr
from rabbit_mq.producer_rabbit import convert_to_audio, send_to_rabbitmq

from database import get_session
from schemas import UserRegistration, UserVerifyCode
from models import ConfirmationCode, User
from random import randint as randint
from sqlmodel import Session, select
from bcrypt import hashpw, gensalt, checkpw
from dotenv import load_dotenv

from utils import send_email
import os

load_dotenv()

CODE_EXPIRATION_TIME = os.getenv("CODE_EXPIRATION_TIME")
CODE_REPEAT_RESPONSE_TIME = os.getenv("CODE_REPEAT_RESPONSE_TIME")

router = APIRouter()

@router.post("/register")
async def register_user(user: UserRegistration, session: Session = Depends(get_session)):
    """
    1. Проверяем, есть ли такой email в базе
    2. Создаём 4-значный код подтверждения
    3. Отправляем код на email
    4. Сохраняем код в БД
    """
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже зарегистрирован")
    
    confirmation_code = str(randint(1000, 9999))

    hashed_password = hashpw(user.password.encode('utf-8'), gensalt())
    db_user = User(email=user.email, password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    expires_at = datetime.now() + timedelta(minutes=int(CODE_EXPIRATION_TIME))
    db_code = ConfirmationCode(
        user_id=db_user.id,
        code=confirmation_code,
        expires_at=expires_at
    )
    session.add(db_code)
    session.commit()
    session.refresh(db_code)
    
    send_email(
        dest_email=user.email, 
        subject_text="Код подтверждения регистрации в сервисе SpeechInsight",
        email_text=f'Ваш код подтверждения: {confirmation_code}'
    )
    return f"message: Код подтверждения отправлен на почту пользователя {user}, {confirmation_code}"

# @router.post("/register/verify_code")
# async def verify_code(data: UserVerifyCode, session: Session = Depends(get_session)):
#     """
#     1. Проверяем, есть ли код в базе
#     2. Проверяем, совпадает ли код и не истёк ли он
#     3. Если всё ок – удаляем код из базы и завершаем регистрацию
#     """
 
#     db_code = session.exec(
#         select(ConfirmationCode).where(ConfirmationCode.user_id == select(User.id).where(User.email == data.email))
#     ).first()

#     if not db_code:
#         raise HTTPException(status_code=404, detail="Код подтверждения не найден")

#     if db_code.code != data.code:
#         raise HTTPException(status_code=400, detail="Неверный код подтверждения")
    
#     if db_code.expires_at < datetime.now():
#         raise HTTPException(status_code=400, detail="Код истёк, запросите новый")

#     session.delete(db_code)
#     session.commit()

#     return {"message": "Регистрация успешно завершена!"}


# @router.post("/register/resend_code")
# async def resend_code(email: UserVerifyCode, session: Session = Depends(get_session)):
#     """
#     1. Проверяем, есть ли пользователь
#     2. Если код ещё не истёк – не отправляем новый
#     3. Если истёк – создаём новый и отправляем
#     """
#     db_user = session.exec(select(UserVerifyCode).where(UserVerifyCode.email == email)).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="Пользователь не найден")

#     db_code = session.exec(select(ConfirmationCode).where(ConfirmationCode.user_id == db_user.id)).first()
#     if db_code and (datetime.now() - db_code.create_at) > :
#         raise HTTPException(status_code=400, detail="Код ещё действителен, повторите попытку позже")

#     # Генерируем новый код
#     new_code = str(randint(1000, 9999))

#     # Обновляем или создаём код
#     if db_code:
#         db_code.code = new_code
#         db_code.expires_at = datetime.now() + CODE_EXPIRATION_TIME
#     else:
#         db_code = ConfirmationCode(
#             user_id=db_user.id,
#             code=new_code,
#             expires_at=datetime.utcnow() + CODE_EXPIRATION_TIME
#         )
#         session.add(db_code)

#     session.commit()

#     # Отправляем новый код
#     send_email(
#         dest_email=email,
#         subject="Новый код подтверждения",
#         email_text=f"Ваш новый код подтверждения: {new_code}"
#     )

#     return {"message": "Новый код отправлен на почту"}

# @router.post("/login", response_model=User1)
# async def login(user: UserLogin):
"""
Если пользователь в статусе disable or banned, то пользователь не может авторизироваться.
"""
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
