"""Бюджеты по категориям и контроль превышения лимита."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, func, select

from app.auth.dependencies import get_current_user
from app.models import Budget, Category, Transaction, TransactionType, User
from app.schemas import (
    BudgetCreate,
    BudgetRead,
    BudgetReadWithCategory,
    BudgetStatus,
    BudgetUpdate,
)
from db import get_session

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def _get_own_budget(budget_id: int, session: Session, current_user: User) -> Budget:
    budget = session.get(Budget, budget_id)
    if budget is None or budget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Бюджет не найден")
    return budget


def _spent_for_budget(session: Session, budget: Budget) -> float:
    """Сумма расходов по категории бюджета внутри его периода."""
    total = session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0.0))
        .where(Transaction.user_id == budget.user_id)
        .where(Transaction.category_id == budget.category_id)
        .where(Transaction.type == TransactionType.expense)
        .where(Transaction.spent_at >= budget.period_start)
        .where(Transaction.spent_at <= budget.period_end)
    ).one()
    return float(total or 0.0)


def _build_status(session: Session, budget: Budget) -> BudgetStatus:
    spent = _spent_for_budget(session, budget)
    category = session.get(Category, budget.category_id)
    usage = (spent / budget.limit_amount * 100) if budget.limit_amount else 0.0
    return BudgetStatus(
        budget_id=budget.id,
        category_name=category.name if category else "—",
        limit_amount=budget.limit_amount,
        spent_amount=round(spent, 2),
        remaining=round(budget.limit_amount - spent, 2),
        usage_percent=round(usage, 2),
        is_exceeded=spent > budget.limit_amount,
    )


@router.get("/", response_model=List[BudgetReadWithCategory])
def list_budgets(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Budget]:
    """Список бюджетов с вложенной категорией."""
    return list(
        session.exec(select(Budget).where(Budget.user_id == current_user.id)).all()
    )


@router.get("/status", response_model=List[BudgetStatus])
def budgets_status(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[BudgetStatus]:
    """Уведомления о превышении: сколько потрачено по каждому бюджету."""
    budgets = session.exec(
        select(Budget).where(Budget.user_id == current_user.id)
    ).all()
    return [_build_status(session, budget) for budget in budgets]


@router.get("/{budget_id}", response_model=BudgetReadWithCategory)
def get_budget(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Budget:
    return _get_own_budget(budget_id, session, current_user)


@router.get("/{budget_id}/status", response_model=BudgetStatus)
def get_budget_status(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BudgetStatus:
    return _build_status(session, _get_own_budget(budget_id, session, current_user))


@router.post("/", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    data: BudgetCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Budget:
    category = session.get(Category, data.category_id)
    if category is None or category.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Некорректный category_id")
    if data.period_end < data.period_start:
        raise HTTPException(
            status_code=400, detail="period_end не может быть раньше period_start"
        )

    budget = Budget(**data.model_dump(), user_id=current_user.id)
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@router.patch("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    data: BudgetUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Budget:
    budget = _get_own_budget(budget_id, session, current_user)
    updates = data.model_dump(exclude_unset=True)
    category_id = updates.get("category_id", budget.category_id)
    category = session.get(Category, category_id)
    if category is None or category.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Некорректный category_id")
    period_start = updates.get("period_start", budget.period_start)
    period_end = updates.get("period_end", budget.period_end)
    if period_end < period_start:
        raise HTTPException(
            status_code=400, detail="period_end не может быть раньше period_start"
        )
    for field, value in updates.items():
        setattr(budget, field, value)
    session.add(budget)
    session.commit()
    session.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    budget = _get_own_budget(budget_id, session, current_user)
    session.delete(budget)
    session.commit()
