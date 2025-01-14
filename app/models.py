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
    __tablename__ ="user"
    id: int = Field(primary_key=True, unique=True)
    email: str = Field(index=True, unique=True)
    password: bytes
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})
    balance: int = Field(default=100)
    role: str = Field(default="user")
    status: str = Field(default="disable")

    transactions: Optional[List["TransactionAudio"]] = Relationship(back_populates="user", cascade_delete=True)
    requests: Optional[List["RequestAudio"]] = Relationship(back_populates="user", cascade_delete=True)
    confirmation_code: Optional["ConfirmationCode"] = Relationship(back_populates="user", cascade_delete=True)

class ConfirmationCode(SQLModel, table=True):
    __tablename__ = "confirmationcode"
    """
    Хранит коды подтверждения для регистарции в сервисе
    code 4-значный код
    expires_at Время истечения кода
    """
    id: int = Field(primary_key=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    code: str  # 4-значный код
    expires_at: datetime  # Время истечения кода
    create_at: datetime = Field(default_factory=datetime.now)
    user: Optional[User] = Relationship(back_populates="confirmation_code")


class TransactionAudio(SQLModel, table=True):
    """
    amount Может быть как положительной (пополнение), так и отрицательной (списание)
    amount_type Описание транзакции (например, "Пополнение баланса", "Запрос к ML сервису")
    """
    __tablename__ = "transactionaudio"

    id: int = Field(primary_key=True, unique=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    amount: int  
    amount_type: str  
    create_at: datetime = Field(default_factory=datetime.now)
    user: Optional[User] = Relationship(back_populates="transactions")
    request_id: Optional[int] = Field(foreign_key="requestaudio.id", nullable=True)
    request: Optional["RequestAudio"] = Relationship(back_populates="transactions")

class RequestAudio(SQLModel, table=True):
    __tablename__ = "requestaudio"
    """
    status_request True или False, если True, то транскрибация успешная, если false, то нет
    output_text, если is_success true, то содержит транскрибацию, иначе содержит ошибку
    cost стоимость транзакции в рублях фиксированна 
    """
    id: int = Field(primary_key=True, unique=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    file_name: str
    output_text: Optional[str]  
    created_at: datetime = Field(default_factory=datetime.now)
    is_success: Optional[bool] = Field(default=False)
    original_format: str
    transactions: Optional[List["TransactionAudio"]] = Relationship(back_populates="request", cascade_delete=True)
    user: Optional[User] = Relationship(back_populates="requests")
