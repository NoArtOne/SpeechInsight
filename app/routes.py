from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import User, MLModel, TransactionHistory, MLTask
from app.database import SessionLocal, engine
from app.schemas import UserCreate, UserLogin, TransactionCreate, MLTaskCreate
from app.crud import get_user_by_username, create_user, authenticate_user, add_balance, get_balance, get_transaction_history, create_transaction, create_ml_task, get_ml_task_result

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register/")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)

@router.post("/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user.username, user.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"username": user.username, "balance": user.balance}

@router.post("/add_balance/")
def add_balance(transaction: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return add_balance(db=db, user_id=current_user.id, amount=transaction.amount)

@router.get("/balance/")
def get_balance(current_user: User = Depends(get_current_user)):
    return get_balance(current_user.id)

@router.get("/transaction_history/")
def get_transaction_history(current_user: User = Depends(get_current_user)):
    return get_transaction_history(current_user.id)

@router.post("/ml_task/")
def create_ml_task(task: MLTaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_ml_task(db=db, user_id=current_user.id, task_data=task.task_data)

@router.get("/ml_task_result/{task_id}")
def get_ml_task_result(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_ml_task_result(db=db, task_id=task_id)
