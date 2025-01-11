from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists
from sqlmodel import SQLModel, Session
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus


load_dotenv()

# DB_HOST = os.getenv("DB_HOST")
DB_HOST = "localhost"
DB_NAME = os.getenv("DB_NAME")
DB_PASS = os.getenv("DB_PASS")
DB_USER = os.getenv("DB_USER")
DB_PORT = os.getenv("DB_PORT")

encoded_password = quote_plus(DB_PASS)
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(DATABASE_URL)
engine = create_engine(DATABASE_URL)

if not database_exists(engine.url):
    create_database(engine.url)
    print("New Database Created" + str(database_exists(engine.url)))
else:
    print("Database Already Exists")

def init_db():
    # SQLModel.metadata.drop_all(engine)
    # SQLModel.metadata.create_all(engine)
    pass
    
def get_session():
    with Session(engine) as session:
        yield session
