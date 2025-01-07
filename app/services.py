from sqlalchemy.orm import Session
from app.models import User, TransactionHistory, MLTask
from app.schemas import UserCreate, TransactionCreate, MLTaskCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not pwd_context.verify(password, user.password):
        return False
    return user

def add_balance(db: Session, user_id: int, amount: float):
    user = db.query(User).filter(User.id == user_id).first()
    user.balance += amount
    db.commit()
    db.refresh(user)
    return user.balance

def get_balance(user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    return user.balance

def get_transaction_history(user_id: int):
    return db.query(TransactionHistory).filter(TransactionHistory.user_id == user_id).all()

def create_transaction(db: Session, transaction: TransactionCreate, user_id: int):
    db_transaction = TransactionHistory(user_id=user_id, transaction_type=transaction.transaction_type, amount=transaction.amount)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def create_ml_task(db: Session, task: MLTaskCreate, user_id: int):
    db_task = MLTask(user_id=user_id, task_data=task.task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_ml_task_result(db: Session, task_id: int):
    task = db.query(MLTask).filter(MLTask.id == task_id).first()
    return task.result
