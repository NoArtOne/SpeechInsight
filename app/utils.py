import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

from schemas import CheckEmail

load_dotenv()

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

# Функция отправки письма
def send_email(dest_email: str, subject_text: str, email_text: str):
    """
    # Использование функции
    send_email(
        "futurehouseprogressive@gmail.com",
        "Тестирую отправку код авторизации для подтверждения пароля",
        "Используй для регистрации или восстановления пароля этот код: 2187"
    )
    ARG: 
        dest_mail кому отправляем
        subject заголовок (header) письма
        email_text текст (body) письма  
    """
    msg = EmailMessage()
    msg["From"] = SMTP_EMAIL
    msg["To"] = dest_email
    msg["Subject"] = subject_text
    msg.set_content(email_text, subtype="plain", charset="utf-8") 

    # Подключаемся к серверу
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)

from datetime import datetime, timedelta

def how_time_has_passed(start_time: datetime, reference_time: int) -> tuple:
    """
    Принимает start_time в формате datetime и считает, сколько прошло времени
    с момента указаного в start_time, а также принимает переменную reference_time
    (в секундах).
    Если прошедшее время превышает reference_time, возвращает True и прошедшее время.
    Иначе, возвращает False и прошедшее время.
    
    ARG:
        start_time: datetime
        reference_time: int (секунды)
        
    RETURNS:
        tuple(bool, timedelta)
    """
    current_time = datetime.now()
    elapsed_time = current_time - start_time
    is_expired = elapsed_time > timedelta(seconds=reference_time)
    return (is_expired, elapsed_time)