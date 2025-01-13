from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
from datetime import timedelta, datetime
from typing import Optional
from starlette import status

#Локальные импорты
from schemas import TokenData

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Добавить для create_access_token schemas
def create_access_token(email: str, id: int):
    data = {"email": email, "id": id}
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str = Depends(oauth2_scheme)):
    """
    email: str = payload.get("email")
    id: int = payload.get("id")
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        id: int = payload.get("id")
        if email is None or id is None:
            raise credentials_exception
        token_data = TokenData(id=id, email=email)

    except JWTError:
        raise credentials_exception
    return token_data
