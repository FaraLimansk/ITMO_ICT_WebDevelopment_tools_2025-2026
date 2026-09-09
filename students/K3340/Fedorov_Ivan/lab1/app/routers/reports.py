"""Аналитика: отчёт за период и структура трат по категориям."""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.auth.dependencies import get_current_user
from app.models import Category, Transaction, TransactionType, User
from app.schemas import CategorySummary, PeriodReport
from db import get_session

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary", response_model=PeriodReport)
def period_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PeriodReport:
    """Сводка по периоду: доходы, расходы, сальдо и доли категорий в расходах.

    По умолчанию — последние 30 дней.
    """
    if date_to is None:
        date_to = date.today()
    if date_from is None:
        date_from = date_to - timedelta(days=30)

    def _total(tx_type: TransactionType) -> float:
        value = session.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0))
            .where(Transaction.user_id == current_user.id)
            .where(Transaction.type == tx_type)
            .where(Transaction.spent_at >= date_from)
            .where(Transaction.spent_at <= date_to)
        ).one()
        return float(value or 0.0)

    total_income = _total(TransactionType.income)
    total_expense = _total(TransactionType.expense)

    # Группировка расходов по категориям одним SQL-запросом (LEFT JOIN + GROUP BY)
    rows = session.exec(
        select(
            Transaction.category_id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), 0.0),
        )
        .join(Category, isouter=True)
        .where(Transaction.user_id == current_user.id)
        .where(Transaction.type == TransactionType.expense)
        .where(Transaction.spent_at >= date_from)
        .where(Transaction.spent_at <= date_to)
        .group_by(Transaction.category_id, Category.name)
    ).all()

    by_category: List[CategorySummary] = [
        CategorySummary(
            category_id=category_id,
            category_name=name or "Без категории",
            total=round(float(total), 2),
            share_percent=(
                round(float(total) / total_expense * 100, 2) if total_expense else 0.0
            ),
        )
        for category_id, name, total in rows
    ]
    by_category.sort(key=lambda item: item.total, reverse=True)

    return PeriodReport(
        period_start=date_from,
        period_end=date_to,
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        balance=round(total_income - total_expense, 2),
        by_category=by_category,
    )
