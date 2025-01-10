"""
Модели представляют структуру данных и предоставляют методы 
для взаимодействия с базой данных, что упрощает управление данными и их изменение.
"""

from sqlmodel import SQLModel, Field, ForeignKey, Relationship
from typing import List, Optional
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, unique=True)
    email: str = Field(index=True, unique=True)
    password: bytes
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})
    balance: int = Field(default=100)
    role: str = Field(default="user")
    # transactions: List["Transaction"] = Relationship(back_populates="user")

# class Transaction(SQLModel, table=True):
#     id: int = Field(default=None, primary_key=True, index=True)
#     user_id: int = Field(ForeignKey("users.id"))
#     amount = Field(Integer)
#     resulting_balance: int

#     user = relationship("User", back_populates="transactions")

# User.transactions = relationship("Transaction", order_by=Transaction.id, back_populates="user")
