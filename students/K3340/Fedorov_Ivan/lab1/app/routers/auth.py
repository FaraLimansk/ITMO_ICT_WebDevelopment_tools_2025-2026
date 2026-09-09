"""Регистрация и выдача JWT."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, or_, select

from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.models import Category, CategoryKind, User
from app.schemas import Token, UserCreate, UserLogin, UserRead
from db import get_session

router = APIRouter(prefix="/auth", tags=["Auth"])

DEFAULT_CATEGORIES = [
    ("Зарплата", CategoryKind.income),
    ("Продукты", CategoryKind.expense),
    ("Транспорт", CategoryKind.expense),
    ("Развлечения", CategoryKind.expense),
]


@router.post(
    "/register", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
def register(data: UserCreate, session: Session = Depends(get_session)) -> User:
    """Создаёт пользователя и набор базовых категорий."""
    exists = session.exec(
        select(User).where(
            or_(User.username == data.username, User.email == data.email)
        )
    ).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким username или email уже существует",
        )

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    # удобство: сразу заводим типовые категории для нового пользователя
    for name, kind in DEFAULT_CATEGORIES:
        session.add(Category(name=name, kind=kind, user_id=user.id))
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, session: Session = Depends(get_session)) -> Token:
    """Проверяет логин/пароль и выдаёт access-токен."""
    user = session.exec(
        select(User).where(User.username == data.username)
    ).first()
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные логин или пароль",
        )
    return Token(access_token=create_access_token(user.id, user.username))


@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    """Та же авторизация, но в формате form-data — для кнопки Authorize в Swagger."""
    return login(
        UserLogin(username=form_data.username, password=form_data.password),
        session,
    )
