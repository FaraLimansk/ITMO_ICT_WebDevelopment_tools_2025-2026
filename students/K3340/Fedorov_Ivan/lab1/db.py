"""Подключение к базе данных и выдача сессий."""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

# Строка подключения берётся из .env (переменная DB_ADMIN)
DB_URL: str = os.getenv(
    "DB_ADMIN",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/finance_db",
)

SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"
engine = create_engine(DB_URL, echo=SQL_ECHO)


def init_db() -> None:
    """Создать таблицы напрямую из моделей (используется в практике 1.2).

    В боевом варианте схему раскатывает Alembic, поэтому вызов не обязателен.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI-зависимость: одна сессия на один HTTP-запрос."""
    with Session(engine) as session:
        yield session
