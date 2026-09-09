"""Профиль пользователя."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.auth.password import hash_password, verify_password
from app.models import User
from app.schemas import PasswordChange, UserRead, UserReadFull
from db import get_session

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Краткий профиль текущего пользователя."""
    return current_user


@router.get("/me/full", response_model=UserReadFull)
def get_me_full(current_user: User = Depends(get_current_user)) -> User:
    """Профиль со вложенными счетами, категориями, бюджетами и целями."""
    return current_user


@router.get("/", response_model=List[UserRead])
def list_users(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[User]:
    """Список пользователей с пагинацией."""
    return list(session.exec(select(User).offset(skip).limit(limit)).all())


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )
    return user


@router.patch("/me/password", response_model=UserRead)
def change_password(
    data: PasswordChange,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    """Смена пароля с проверкой старого."""
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Старый пароль неверен"
        )
    current_user.hashed_password = hash_password(data.new_password)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user
