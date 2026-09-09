"""Зависимости FastAPI для защиты эндпоинтов."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.auth.jwt import decode_access_token
from app.models import User
from db import get_session

# tokenUrl нужен только для кнопки Authorize в Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Достаёт пользователя из JWT и проверяет, что он ещё активен."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверный или истёкший токен",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = session.get(User, int(user_id))
    if user is None or not user.is_active:
        raise credentials_error
    return user
