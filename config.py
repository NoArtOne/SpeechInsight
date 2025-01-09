import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")


# from pydantic_settings import BaseSettings, SettingsConfigDict
# from functools import lru_cache
# from typing import Optional


# class Settings(BaseSettings):
#     DB_HOST: Optional[str] = None
#     DB_PORT: Optional[int] = None
#     DB_USER: Optional[str] = None
#     DB_PASS: Optional[str] = None
#     DB_NAME: Optional[str] = None

#     SECRET_KEY: Optional[str] = None
#     ALGORITHM: Optional[str] = None
#     ACCESS_TOKEN_EXPIRE_MINUTES: Optional[str] = None

#     @property
#     def DATABASE_URL(self):
#         return f'postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

#     model_config = SettingsConfigDict(env_file='.env')


# @lru_cache()
# def get_settings() -> Settings:
#     return Settings()