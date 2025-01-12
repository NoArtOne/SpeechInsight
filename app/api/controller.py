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

from utils import how_time_has_passed, send_email
import os

#TODO вынсти все load_dotenv() в config.py  
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
    #Исключили из повторной регистрации забаненных по такому адресу и активных
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user and existing_user.status == "banned" or existing_user and existing_user.status == "active":
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже зарегистрирован")
    
    #Для облегчения удаляем тех, кто не активировался до конца и идем дальше по процессу регистрации
    if existing_user and existing_user.status == "disable":
        session.delete(db_code)
        session.commit()

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

@router.post("/register/verify_code")
async def verify_code(data: UserVerifyCode, session: Session = Depends(get_session)):
    """
    1. Проверяем, есть ли код в базе
    2. Проверяем, совпадает ли код и не истёк ли он
        2.1. Если код истёк, он авт. перезапрашивается
    3. Если всё ок – удаляем код из базы и завершаем регистрацию
    """
    db_user = session.exec(select(User).where(User.email == data.email)).first()
    if not db_user:
        print("Пользователь не найден")
        raise HTTPException(status_code=404, detail="Что-то пошло не так. Попробуйте зарегистрироваться \
                            ещё раз позднее!")
    db_code = session.exec(select(ConfirmationCode).where(ConfirmationCode.user_id == db_user.id)).first()

    if db_code:
        is_expired, elapsed_time = how_time_has_passed(db_code.create_at, CODE_EXPIRATION_TIME)
        if is_expired==True:
            resend_code(email=data.email, session=session)
            #TODO print("Реализовать устаревание и удаление кода авторизации") celory
            raise HTTPException(status_code=404, detail="Код подтверждения устарел, прошло более 30 минут.\
                                 На вашу почту отправлен новый код авторизации")
        elif is_expired==False:
            session.delete(db_code)
            session.commit()
            db_user = ConfirmationCode(status="activate")
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            return {"message": "Регистрация успешно завершена!"}

    if not db_code:
        resend_code(email=data.email, session=session)
        return {
            "message": "Код подтверждения устарел. На вашу почту отправлен новый код авторизации.",
        }
    if not db_code:
        raise HTTPException(status_code=408, detail="Код подтверждения устарел, на вашу почту отправлен \
                            новый код")

    if db_code.code != data.code:
        raise HTTPException(status_code=400, detail="Неверный код подтверждения. Попробуйте ещё раз или \
                            запросить код повторно")

 
@router.post("/register/resend_code")
async def resend_code(data: UserVerifyCode, session: Session = Depends(get_session)):
    """
    1. Проверяем, есть ли пользователь
    2. Если код ещё не истёк – не отправляем новый
    3. Если истёк – создаём новый и отправляем
    """
    db_user = session.exec(select(User).where(User.email == data.email)).first()
    if not db_user:
        print("Пользователь не найден")
        raise HTTPException(status_code=404, detail="Что-то пошло не так. Попробуйте зарегистрироваться \
                            ещё раз позднее!")

    db_code = session.exec(select(ConfirmationCode).where(ConfirmationCode.user_id == db_user.id)).first()
    if db_code:
        is_expired, elapsed_time = how_time_has_passed(db_code.create_at, CODE_REPEAT_RESPONSE_TIME)
        if is_expired==True:

            new_code = str(randint(1000, 9999))

            if db_code:
                db_code.code = new_code
                db_code.expires_at = datetime.now() + CODE_EXPIRATION_TIME
            else:
                db_code = ConfirmationCode(
                    user_id=db_user.id,
                    code=new_code,
                    expires_at=datetime.now() + CODE_EXPIRATION_TIME
                )

            session.add(db_code)
            session.commit()

            send_email(
            dest_email=data.email,
            subject="Новый код подтверждения",
            email_text=f"Ваш новый код подтверждения: {new_code}"
            )
            return {
                f"message: Код подтверждения успешно отправлен на вашу почту отправлен новый код \
                    авторизации, новый код вы сможете запросить через 30 секунд"
                }
        
        elif is_expired==False:
            raise HTTPException(status_code=425, detail=f"Вы запрашивали код авторизации \
                                {timedelta(seconds=datetime.now())-elapsed_time} секунд назад, подождите")


# @router.post("/login", response_model=User)
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
