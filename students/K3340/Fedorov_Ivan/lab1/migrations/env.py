"""Конфигурация Alembic для SQLModel."""

import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# добавляем корень проекта в sys.path, чтобы работал импорт app.models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models  # noqa: E402,F401  (важно: регистрирует таблицы в metadata)

load_dotenv()

config = context.config

# подставляем URL из .env, чтобы не держать пароль в alembic.ini
config.set_main_option("sqlalchemy.url", os.getenv("DB_ADMIN", ""))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Генерация SQL без подключения к БД."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Обычный режим: подключаемся и применяем миграции."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
