from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import SQLModel, Session
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

# Загружаем переменные окружения
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PASS = os.getenv("DB_PASS")
DB_USER = os.getenv("DB_USER")
DB_PORT = os.getenv("DB_PORT")


encoded_password = quote_plus(DB_PASS)

DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"Подключение к БД: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=True)  # echo=True для отладки SQL-запросов

def init_db():
    """
    Функция инициализации базы данных.
    - Проверяет, существует ли база
    - Создаёт её, если её нет
    - Для дропа в init_db необходимо раскомментировать # SQLModel.metadata.drop_all(bind=engine)
    """
    # SQLModel.metadata.drop_all(bind=engine)
    if not database_exists(engine.url):
        create_database(engine.url)
        
        print("Новая база данных создана!")
    else:
        print("База данных уже существует.")

    # SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
    print("Таблицы успешно пересозданы.")


def get_session():
    """
    Генератор сессий для взаимодействия с БД.
    """
    with Session(engine) as session:
        yield session