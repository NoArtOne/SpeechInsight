
"""
Контроллер получает запросы от клиента, использует схемы для валидации данных, взаимодействует
с моделями для выполнения операций с базой данных и возвращает ответ клиенту/
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from schemas import UserResponse
from services import register_user
from auth import verify_access_token

from database import get_session
from schemas import UserResponse, UserRegistration
from models import User

from sqlmodel import Session
from bcrypt import hashpw, gensalt, checkpw


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# @router.get("/register")
# async def register_form(request: Request):
#     return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register_user(user: UserRegistration, session: Session = Depends(get_session)):
    hashed_password = hashpw(user.password.encode('utf-8'), gensalt())
    db_user = User(email=user.email, password=hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return user


# @router.post("/login", response_model=User1)
# async def login(user: UserLogin):
#     return await login_user(user)

@router.post("/admin/create_user")
async def create_user(user: UserRegistration, session: Session = Depends(get_session)):
    hashed_password = hashpw(user.password.encode('utf-8'), gensalt())
    db_user = User(email=user.email, password=hashed_password)
    print(db_user, hashed_password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return user

# @router.get("/me/", response_model=User)
# async def read_users_me(token_data: TokenData = Depends(verify_access_token)):
#     user = session.query(User).filter(User.email == token_data.email).first()
#     if user is None:
#         #todo raise пользователя нет
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# @router.get("/balance", response_model=Transaction)
# async def balance(current_user: User1 = Depends(get_current_user)):
#     return await get_balance(current_user)

# @router.post("/top_up", response_model=Transaction)
# async def top_up(amount: int, current_user: User1 = Depends(get_current_user)):
#     return await top_up_balance(current_user, amount)

# @router.post("/predict", response_model=PredictionResponse)
# async def predict(request: PredictionRequest, current_user: User1 = Depends(get_current_user)):
#     return await make_prediction(request, current_user)

# @router.get("/history", response_model=list[PredictionResponse])
# async def history(current_user: User1 = Depends(get_current_user)):
#     return await get_history(current_user)
