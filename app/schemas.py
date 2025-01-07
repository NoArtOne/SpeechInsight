from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TransactionCreate(BaseModel):
    transaction_type: str
    amount: float

class MLTaskCreate(BaseModel):
    task_data: str
