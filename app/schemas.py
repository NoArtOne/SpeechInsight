"""
Схемы обеспечивают валидацию и сериализацию данных, что помогает поддерживать
 целостность данных и упрощает взаимодействие с клиентами.
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UserRegistration(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    # password: str
    balance: int
    created_at: datetime
    updated_at: datetime
    role: str

    #Нужно для тех схем, которые общаются с базой данных
    class Config:
        from_attributes = True
#Избыточно
# class Supervisor(BasicUserSchemas):
#     id: int
#     email: str
#     password: str
#     balance: int
#     role: str

# class UserBase(BaseModel):
#     email: str

# class UserCreate(UserBase):
#     password: str

# class UserLogin(UserBase):
#     password: str

# class User1(UserBase):
#     id: int
#     balance: int

#     class Config:
#         from_attributes = True

# class Transaction(BaseModel):
#     amount: int
#     balance: int

# class PredictionRequest(BaseModel):
#     file: bytes
#     filename: str

# class PredictionResponse(BaseModel):
#     text: str
#     participants: List[str]
#     credits_spent: int



