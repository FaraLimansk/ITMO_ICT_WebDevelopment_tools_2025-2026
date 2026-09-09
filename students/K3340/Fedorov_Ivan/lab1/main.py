"""Точка входа приложения FastAPI.

Запуск: uvicorn main:app --reload
"""

from fastapi import FastAPI

from app.routers import (
    accounts,
    auth,
    budgets,
    categories,
    goals,
    reports,
    tags,
    transactions,
    users,
)

app = FastAPI(
    title="Personal Finance Service",
    description=(
        "Лабораторная работа 1: сервис управления личными финансами на FastAPI + "
        "SQLModel + PostgreSQL + Alembic с JWT-авторизацией"
    ),
    version="1.0.0",
)

# Каждый роутер отвечает за свою предметную область
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(tags.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(reports.router)


@app.get("/", tags=["Service"])
def root() -> dict[str, str]:
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "docs": "/docs"}


@app.get("/health", tags=["Service"])
def health() -> dict[str, str]:
    """Простой health-check для Docker и систем мониторинга."""
    return {"status": "healthy"}
