from datetime import datetime, timedelta
import logging
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    FastAPI,
    File,
    UploadFile
)
from fastapi.templating import Jinja2Templates
from auth import create_access_token, verify_access_token
from rabbit_mq.producer_rabbit import convert_to_audio, send_to_rabbitmq
from fastapi.openapi.utils import get_openapi
from database import get_session
from schemas import (
    LoginRequest,
    RequestAudioResponse,
    TokenData,
    TransactionAudioResponse,
    UserRegistration,
    UserRequest,
    UserResponse,
    UserVerifyCode
)
from models import (
    ConfirmationCode, 
    RequestAudio, 
    TransactionAudio, 
    User
)
from random import randint
from sqlmodel import Session, select
from bcrypt import hashpw, gensalt, checkpw
from dotenv import load_dotenv
from starlette.responses import HTMLResponse, RedirectResponse
from utils import how_time_has_passed, send_email
import os

load_dotenv()
CODE_EXPIRATION_TIME = int(os.getenv("CODE_EXPIRATION_TIME", 30))  # В минутах
CODE_REPEAT_RESPONSE_TIME = int(os.getenv("CODE_REPEAT_RESPONSE_TIME", 30))  # В секундах
AMOUNT = int(os.getenv("AMOUNT", 1)) 

router = APIRouter()

templates = Jinja2Templates(directory="public")

logger = logging.getLogger(__name__)

# --- Вспомогательная функция для переотправки кода по email ---
def resend_code_email(email: str, session: Session):
    """
    Функция для повторной отправки кода подтверждения.
    """
    db_user = session.exec(select(User).where(User.email == email)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Создаём или обновляем код подтверждения
    confirmation_code = str(randint(1000, 9999))
    expires_at = datetime.now() + timedelta(minutes=CODE_EXPIRATION_TIME)

    db_code = session.exec(select(ConfirmationCode).where(ConfirmationCode.user_id == db_user.id)).first()
    if db_code:
        db_code.code = confirmation_code
        db_code.expires_at = expires_at
    else:
        db_code = ConfirmationCode(
            user_id=db_user.id,
            code=confirmation_code,
            expires_at=expires_at
        )
        session.add(db_code)
    
    session.commit()
    session.refresh(db_code)
    
    send_email(
        dest_email=db_user.email, 
        subject_text="Новый код подтверждения регистрации в сервисе SpeechInsight",
        email_text=f"Ваш новый код подтверждения: {confirmation_code}"
    )

# --- HTML Endpoints ---

@router.get("/", response_class=HTMLResponse)
async def read_root():
    file_path = os.path.join(os.path.dirname(__file__), "../public", "register.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@router.get("/verify_code", response_class=HTMLResponse)
async def verify_code_page(request: Request):
    file_path = os.path.join(os.path.dirname(__file__), "../public", "verify_code.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    file_path = os.path.join(os.path.dirname(__file__), "../public", "login.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@router.get("/upload_audio", response_class=HTMLResponse)
async def upload_audio_page(request: Request):
    return templates.TemplateResponse("upload_audio.html", {"request": request})

@router.get("/user_profile", response_class=HTMLResponse)
async def user_profile_page():
    file_path = os.path.join(os.path.dirname(__file__), "../public", "user_profile.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@router.get("/top_up", response_class=HTMLResponse)
async def top_up_page(request: Request):
    return templates.TemplateResponse("top_up.html", {"request": request})

@router.get("/transactions_page", response_class=HTMLResponse) 
async def transactions_page_route(request: Request):
    return templates.TemplateResponse("transactions.html", {"request": request})

@router.get("/audios_page", response_class=HTMLResponse) 
async def audios_page_route(request: Request):
    return templates.TemplateResponse("audios.html", {"request": request})

@router.get("/audios_page/{id}", response_class=HTMLResponse)
async def audio_detail_page(request: Request, id: int):
    return templates.TemplateResponse("audio_detail.html", {"request": request, "audio_id": id})

# --- API Endpoints ---

@router.post("/api/register")
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = UserRegistration(email=email, password=password)
    """
    1. Проверяем, есть ли такой email в базе
    2. Создаём 4-значный код подтверждения
    3. Отправляем код на email
    4. Сохраняем код в БД
    """
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if (
        (existing_user and existing_user.status == "banned") or
        (existing_user and existing_user.status == "active")
    ):
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже зарегистрирован")
    
    # Удаляем пользователя со статусом "disable"
    if existing_user and existing_user.status == "disable":
        session.delete(existing_user)
        session.commit()

    # Генерируем код подтверждения
    confirmation_code = str(randint(1000, 9999))

    # Хешируем пароль
    hashed_password = hashpw(user.password.encode('utf-8'), gensalt())

    logger.info(f"User registered with email: {email}")
    db_user = User(email=user.email, password=hashed_password)
    logger.info(f"db_user: {db_user}")
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Создаём запись подтверждения
    expires_at = datetime.now() + timedelta(minutes=CODE_EXPIRATION_TIME)
    db_code = ConfirmationCode(
        user_id=db_user.id,
        code=confirmation_code,
        expires_at=expires_at
    )
    session.add(db_code)
    session.commit()
    session.refresh(db_code)
    
    # Отправляем код на email
    send_email(
        dest_email=db_user.email, 
        subject_text="Код подтверждения регистрации в сервисе SpeechInsight",
        email_text=f'Ваш код подтверждения: {confirmation_code}'
    )
    
    # Перенаправляем на страницу ввода кода подтверждения
    return RedirectResponse(url="/verify_code", status_code=303)

@router.post("/api/register/verify_code")
async def verify_code(
    email: str = Form(...),
    code: str = Form(...),
    session: Session = Depends(get_session)
):
    """
    1. Проверяем, есть ли код в базе
    2. Проверяем, совпадает ли код и не истёк ли он
        2.1. Если код истёк, он автоматически перезапрашивается
    3. Если всё ок – удаляем код из базы и завершаем регистрацию
    """
    db_user = session.exec(select(User).where(User.email == email)).first()
    if not db_user:
        print("Пользователь не найден")
        raise HTTPException(
            status_code=404,
            detail="Что-то пошло не так. Попробуйте зарегистрироваться ещё раз позже!"
        )
    db_code = session.exec(select(ConfirmationCode).where(ConfirmationCode.user_id == db_user.id)).first()

    if db_code:
        is_expired, elapsed_time = how_time_has_passed(db_code.create_at, CODE_EXPIRATION_TIME * 60)  # Преобразуем минуты в секунды
        if is_expired:
            resend_code_email(email, session)
            session.delete(db_code)
            session.commit()
            raise HTTPException(
                status_code=404, 
                detail="Код подтверждения устарел. Новый код отправлен на вашу почту."
            )
        elif db_code.code != code:
            raise HTTPException(status_code=400, detail="Неверный код подтверждения. Попробуйте ещё раз или запросите новый код.")
        else:
            db_user.status = "active"
            session.delete(db_code)
            session.commit()

            access_token = create_access_token(db_user.email, db_user.id)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "redirect_url": "/user_profile"}


    # Если кода нет, перенаправляем на повторную отправку
    resend_code_email(email, session)
    raise HTTPException(status_code=408, detail="Код подтверждения отсутствует. Новый код отправлен на вашу почту.")

@router.post("/api/register/resend_code")
async def resend_code(
    email: str = Form(...),
    session: Session = Depends(get_session)
):
    """
    1. Проверяем, есть ли пользователь
    2. Если код ещё не истёк – не отправляем новый
    3. Если истёк – создаём новый и отправляем
    """
    db_user = session.exec(select(User).where(User.email == email)).first()
    if not db_user:
        print("Пользователь не найден")
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    db_code = session.exec(select(ConfirmationCode).where(ConfirmationCode.user_id == db_user.id)).first()
    if db_code:
        is_expired, elapsed_time = how_time_has_passed(db_code.create_at, CODE_REPEAT_RESPONSE_TIME)
        if is_expired:
            # Переотправляем код
            resend_code_email(email, session)
            return {"message": "Код подтверждения успешно отправлен на вашу почту. Новый код вы сможете запросить через 30 секунд."}
        else:
            # Вычисляем, сколько времени осталось до следующего запроса
            remaining_time = CODE_REPEAT_RESPONSE_TIME - int(elapsed_time.total_seconds())
            raise HTTPException(status_code=425, detail=f"Вы запрашивали код авторизации {int(elapsed_time.total_seconds())} секунд назад, подождите {max(remaining_time, 1)} секунд.")
    else:
        # Если кода нет, создаём и отправляем новый
        resend_code_email(email, session)
        return {"message": "Код подтверждения успешно отправлен на вашу почту."}

@router.post("/api/users/login/")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == email)).first()
    if user and checkpw(password.encode('utf-8'), user.password):
        access_token = create_access_token(user.email, user.id)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "redirect_url": "/user_profile"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/api/users/me", response_model=UserResponse)
async def get_user_data(
    token_data: TokenData = Depends(verify_access_token),
    session: Session = Depends(get_session),
):
    db_user = session.exec(select(User).where(User.id == token_data.id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return db_user

@router.post("/api/users/top_up")
async def top_up_balance(
    token_data: TokenData = Depends(verify_access_token),
    session: Session = Depends(get_session),
):
    """
    Пополнение баланса пользователя.
    """
    db_user = session.exec(select(User).where(User.id == token_data.id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    db_user.balance += AMOUNT
    session.add(db_user)

    # Создаём запись транзакции
    transaction = TransactionAudio(
        user_id=db_user.id,
        amount=AMOUNT,
        amount_type="Пополнение баланса",
        created_at=datetime.now(),
    )
    session.add(transaction)
    session.commit()
    session.refresh(db_user)
    return {"message": f"Баланс успешно пополнен на {AMOUNT}", "new_balance": db_user.balance}

@router.post("/api/audios")
async def upload_audio(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    token_data: TokenData = Depends(verify_access_token),
):
    """
    Эндпоинт для загрузки файла и отправки аудио в RabbitMQ.
    Кто загружает, что за пользователь и сколько списать у него средств.
    """
    logger.info(f"Начало функции")
    try:
        db_user = session.exec(select(User).where(User.id == token_data.id)).first()
        if not db_user:
            raise HTTPException(
                status_code=404, detail="Токен не действительный, пройдите авторизацию заново"
            )
        logger.info(f"db_user:{db_user}")

        if not file.filename:
            raise HTTPException(status_code=400, detail="Файл не загружен")


        original_name, original_format = os.path.splitext(file.filename)
        original_format = original_format.lstrip(".").lower()
        file_content = await file.read()
        audio_bytes = convert_to_audio(file_content, original_format)
        logger.info(f"original_name:{original_name}")
        db_request = RequestAudio(
            user_id=db_user.id,
            file_name=original_name,
            created_at=datetime.now(),
            original_format=original_format,
        )
        logger.info(f"db_request:{db_request}")
        session.add(db_request)
        session.commit()
        session.refresh(db_request)

        if db_user.balance < AMOUNT:
            raise HTTPException(status_code=402, detail="Недостаточно средств на балансе")
        logger.info(f"Начала создания транзакции")
        db_transaction = TransactionAudio(
            user_id=db_user.id,
            amount=AMOUNT,
            amount_type="Списание средств",
            created_at=datetime.now(),
            request_id=db_request.id,
        )
        logger.info(f"db_transaction:{db_transaction}")

        db_user.balance -= AMOUNT 

        session.add(db_transaction)
        session.add(db_user) 
        session.commit()
        session.refresh(db_transaction)
        send_to_rabbitmq(audio_bytes, original_format, id_audio_users_requests = db_request.id)
    

        return RedirectResponse(url="/user_profile", status_code=303)
    except Exception as inst:
        logger.info(f"{Exception( exc_info=True)}")

@router.get("/api/audios", response_model=list[RequestAudioResponse])
async def get_list_audios(
    session: Session = Depends(get_session), token_data: TokenData = Depends(verify_access_token)
):
    db_user_requests = session.exec(
        select(RequestAudio).where(RequestAudio.user_id == token_data.id)
    ).all()
    if not db_user_requests:
        raise HTTPException(status_code=404, detail="У вас ещё нет транскрипции аудио-файлов")

    return db_user_requests

@router.get("/api/audios/{id}", response_model=RequestAudioResponse)
async def get_audio(
    id: int,
    session: Session = Depends(get_session),
    token_data: TokenData = Depends(verify_access_token),
):
    db_audio = session.exec(
        select(RequestAudio).where(
            RequestAudio.id == id, RequestAudio.user_id == token_data.id
        )
    ).first()

    if db_audio is None:
        raise HTTPException(status_code=404, detail="Аудио-файл не найден")

    return db_audio

@router.get("/api/transactions", response_model=list[TransactionAudioResponse])
async def get_list_transactions(
    session: Session = Depends(get_session),
    token_data: TokenData = Depends(verify_access_token),
):
    db_user_transactions = session.exec(
        select(TransactionAudio).where(TransactionAudio.user_id == token_data.id)
    ).all()

    if not db_user_transactions:
        raise HTTPException(status_code=404, detail="У вас ещё нет транзакций")

    return db_user_transactions

@router.get("/openapi.json")
async def openapi():
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        routes=router.routes,  # Corrected to use router.routes
    )
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Auth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    openapi_schema["security"] = [{"Bearer Auth": []}]  # This is where SecurityRequirement is used.
    return openapi_schema