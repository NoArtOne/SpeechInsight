"""
Модели представляют структуру данных и предоставляют методы 
для взаимодействия с базой данных, что упрощает управление данными и их изменение.
"""

from sqlmodel import SQLModel, Field, ForeignKey, Relationship
from typing import List, Optional
from datetime import datetime


class User(SQLModel, table=True):
    """
    password хешированный 
    """
    id: Optional[int] = Field(primary_key=True, unique=True)
    email: str = Field(index=True, unique=True)
    password: bytes
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})
    balance: int = Field(default=100)
    role: str = Field(default="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    requests: List["Request"] = Relationship(back_populates="user")
    status: str = Field(default="disable")

class ConfirmationCode(SQLModel, table=True):
    """
    Хранит коды подтверждения для регистарции в сервисе
    code 4-значный код
    expires_at Время истечения кода
    """
    id: Optional[int] = Field(primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    code: int  # 4-значный код
    expires_at: datetime  # Время истечения кода
    create_at: datetime = Field(default_factory=datetime.now)

class Transaction(SQLModel, table=True):
    """
    amount Может быть как положительной (пополнение), так и отрицательной (списание)
    amount_type Описание транзакции (например, "Пополнение баланса", "Запрос к ML сервису")
    """
    id: Optional[int] = Field(primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    amount: int  
    amount_type: str  
    create_at: datetime = Field(default_factory=datetime.now)
    user: User = Relationship(back_populates="transactions")
    request_id: Optional[int] = Field(foreign_key="request.id", nullable=True)
    request: Optional["Request"] = Relationship(back_populates="transactions")

class Request(SQLModel, table=True):
    """
    status_request True или False, если True, то транскрибация успешная, если false, то нет
    output_text, если is_success true, то содержит транскрибацию, иначе содержит ошибку
    cost стоимость транзакции в рублях фиксированна 
    """
    id: Optional[int] = Field(primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    file_name: str
    output_text: Optional[str]  
    created_at: datetime = Field(default_factory=datetime.now)
    cost: int  
    transactions: List["Transaction"] = Relationship(back_populates="request")
    user: User = Relationship(back_populates="requests")
    is_success: Optional[bool] = Field(default=False)

