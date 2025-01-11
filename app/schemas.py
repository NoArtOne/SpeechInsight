"""
Схемы обеспечивают валидацию и сериализацию данных, что помогает поддерживать
целостность данных и упрощает взаимодействие с клиентами.

#Нужно для тех схем, которые общаются с базой данных
class Config:
    from_attributes = True
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class TokenData(BaseModel):
    id: int = None
    email: str = None
    
    class Config:
        from_attributes = True

class UserRegistration(BaseModel):
    email: EmailStr
    password: str

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    balance: int
    created_at: datetime
    updated_at: datetime
    role: str

    class Config:
        from_attributes = True
