"""
Схемы обеспечивают валидацию и сериализацию данных, что помогает поддерживать
целостность данных и упрощает взаимодействие с клиентами.

#Нужно для тех схем, которые общаются с базой данных
class Config:
    from_attributes = True
"""
from pydantic import BaseModel, EmailStr, constr
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
    #TODO Call expression not allowed in type expressionPylancereportInvalidTypeForm 
    # password: constr(strip_whitespace=True, min_length=7, regex=r'^(?=.*[\p{L}])(?=.*[@!#$_-]).{7,}$')

    class Config:
        from_attributes = True
    
class UserVerifyCode(BaseModel):
    email: EmailStr
    code: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    balance: int
    created_at: datetime
    updated_at: datetime
    role: str

    class Config:
        from_attributes = True

class CheckEmail(BaseModel):
    email: EmailStr