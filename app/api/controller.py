"""
Контроллер получает запросы от клиента, использует схемы для валидации данных, взаимодействует
с моделями для выполнения операций с базой данных и возвращает ответ клиенту
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, FastAPI, File, UploadFile
from pydantic import EmailStr
from auth import create_access_token, verify_access_token
from rabbit_mq.producer_rabbit import convert_to_audio, send_to_rabbitmq
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.models import SecurityRequirement

from database import get_session
from schemas import LoginRequest, RequestAudioResponse, TokenData, UserRegistration, UserRequest, UserVerifyCode
from models import ConfirmationCode, RequestAudio, TransactionAudio, User
from random import randint as randint
from sqlmodel import Session, select
from bcrypt import hashpw, gensalt, checkpw
from dotenv import load_dotenv
from starlette.responses import HTMLResponse

from utils import how_time_has_passed, send_email
import os


#TODO вынсти все load_dotenv() в config.py  
load_dotenv()
CODE_EXPIRATION_TIME = os.getenv("CODE_EXPIRATION_TIME")
CODE_REPEAT_RESPONSE_TIME = os.getenv("CODE_REPEAT_RESPONSE_TIME")
AMOUT = os.getenv("AMOUT")

router = APIRouter()

@router.get("/")
async def root():
    file_path = os.path.join(os.path.dirname(__file__), '../public', 'register.html')
    return HTMLResponse(open(file_path, "r").read())

@router.get("/login")
async def login():
    return HTMLResponse(open("/login.html", "r").read())

@router.get("/upload_audio")
async def upload_audio():
    return HTMLResponse(open("/upload_audio.html", "r").read())

@router.get("/transactions")
async def transactions():
    return HTMLResponse(open("/transactions.html", "r").read())

@router.post("/api/register")
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
            access_token = create_access_token(db_user.email, db_user.id)
            
            return {"access_token": access_token, "token_type": "bearer"}

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


@router.post("/users/login/")
async def login(request: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(User).filter(User.email == request.email).first()
    if user and checkpw(request.password.encode('utf-8'), user.password):
        access_token = create_access_token(user.email,user.id)
        return {"access_token": access_token, "token_type": "bearer"}
    
    #TODO пользователь не найден 404
    raise HTTPException(status_code=401, detail="Invalid credentials")



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

@router.post("/audios")
async def upload_audio(file: UploadFile = File(...), session: Session = Depends(get_session), token_data: TokenData = Depends(verify_access_token)):
    """
    Эндпоинт для загрузки файла и отправки аудио в RabbitMQ
    Кто загружает, что за пользователь и сколько списать у него средств
    """

    db_user = session.exec(select(User).where(User.user_id == token_data.id)).first()
    if not db_user:
        #TODO сделать перекидывание на login
        raise HTTPException(status_code=404, detail="токен не действительный, пройдите авторизацию заново")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не загружен")

    #Имя загружаемого файла
    file_name_parts = file.split('.')
    original_name = '.'.join(file_name_parts[:-1])
    
    #Перевод файла в байты 
    file_content = await file.read()
    audio_bytes = convert_to_audio(file_content, original_format)

    #формат файла
    original_format = file.filename.split('.')[-1].lower()

    db_request = RequestAudio(
                    user_id=db_user.id,
                    file_name=original_name,
                    created_at=datetime.now(),
                    original_format=original_format
                )

    session.add(db_request)
    session.commit()
    session.refresh(db_request)

    db_transation = TransactionAudio(
        user_id=db_user.id,
        amount=AMOUT,
        amount_type="Списание средств",
        create_at=datetime.now(),
        request_id=db_request.id
    )
    session.add(db_transation)
    session.commit()
    session.refresh(db_transation)

    send_to_rabbitmq(audio_bytes, original_format)

    return {"message": "Файл успешно отправлен в RabbitMQ"}

@router.get("/audios")
async def get_list_audios(session: Session = Depends(get_session), token_data: TokenData = Depends(verify_access_token)):
#TODO взять все запросы принадлежащие пользователю
    db_user_requests = session.exec(select(RequestAudio).where(RequestAudio.user_id == token_data.id)).all()
    if db_user_requests is None:
        raise HTTPException(status_code=404, detail="У вас ещё нет транскрипции аудио-файлов")
    request_json = {
        RequestAudioResponse(id=_object.id, created_at=_object.created_at, file_name=_object.file_name)
        for _object in db_user_requests
    }
        
    return {"message": {request_json}}

@router.get("/audios/{id}")
async def get_audio(id: int, session: Session =Depends(get_session), token_data: TokenData = Depends(verify_access_token)):
#TODO вернуть выбранную пользователем аудио
    db_audio = session.exec(select(RequestAudio).where(RequestAudio.id == id, RequestAudio.user_id == token_data.id)).first()

    if db_audio is None:
        raise HTTPException(status_code=404, detail="Аудио-файл не найден")
    
    return {f"message: {db_audio}"}

@router.get("/transactions")
async def get_list_transactions(session: Session = Depends(get_session), token_data: TokenData = Depends(verify_access_token)):
    # Получаем все транзакции, принадлежащие пользователю
    db_user_transactions = session.exec(select(TransactionAudio).where(TransactionAudio.user_id == token_data.id)).all()

    if not db_user_transactions:
        raise HTTPException(status_code=404, detail="У вас ещё нет транзакций")

    return {"message": db_user_transactions}

@router.get("/openapi.json")
async def openapi():
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Auth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    openapi_schema["security"] = [{"Bearer Auth": []}]
    return openapi_schema



    # id: int = Field(primary_key=True, unique=True)
    # user_id: int = Field(index=True, foreign_key="user.id")
    # file_name: str
    # output_text: Optional[str]  
    # created_at: datetime = Field(default_factory=datetime.now)
    # transactions: List["Transaction"] = Relationship(back_populates="request")
    # user: User = Relationship(back_populates="requests")
    # is_success: Optional[bool] = Field(default=False)
    # original_format: str