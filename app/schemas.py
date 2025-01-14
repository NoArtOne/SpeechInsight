"""
Схемы обеспечивают валидацию и сериализацию данных, что помогает поддерживать
целостность данных и упрощает взаимодействие с клиентами.

#Нужно для тех схем, которые общаются с базой данных
class Config:
    from_attributes = True
"""
from pydantic import BaseModel, EmailStr, constr, validator
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

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 7:
            raise ValueError("Password must be at least 7 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter")
        if not any(char in "!@#$%^&*()" for char in v):
            raise ValueError("Password must contain at least one special character")
        return v
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
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
    status: str

    class Config:
        from_attributes = True


class UserRequest:
    id: int
    user_id: int
    file_name: str
    output_text: Optional[str] = None  # output_text should be optional
    created_at: datetime
    cost: int  
    is_success: bool
    original_format: str

class CheckEmail(BaseModel):
    email: EmailStr

class RequestAudioResponse(BaseModel):
    """
    Нужен для подготовки данных, а именно списка аудио-тексто пользователя
    """

    id: int
    created_at: datetime
    file_name: str
    original_format: str  # Add original_format
    output_text: Optional[str] = None

class TransactionAudioResponse(BaseModel):
    id: int
    amount: int
    amount_type: str
    created_at: datetime
    request_id: Optional[int] = None
    user_id: int  # Include user_id

    class Config:
        from_attributes = True