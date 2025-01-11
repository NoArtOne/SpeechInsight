import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_EMAIL=os.getenv("SMTP_EMAIL")
SMTP_PASSWORD=os.getenv("SMTP_PASSWORD")
SMTP_SERVER=os.getenv("SMTP_SERVER")
SMTP_PORT=int(os.getenv("SMTP_PORT"))

# Функция отправки письма
def send_email(dest_email, subject, email_text):
    """
    # Использование функции
    send_email(
    "futurehouseprogressive@gmail.com",
    "Тестирую отправку код авторизации для подтверждения пароля",
    "Используй для регистрации или восстановления пароля этот код: 2187"
    ARG: 
        dest_mail кому отправляем
        subject заголовок (header) письма
        email_text текст (body) письма  


)
    """
    msg = EmailMessage()
    msg["From"] = SMTP_EMAIL
    msg["To"] = dest_email
    msg["Subject"] = subject
    msg.set_content(email_text, subtype="plain", charset="utf-8") 

    # Подключаемся к серверу
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.send_message(msg)



