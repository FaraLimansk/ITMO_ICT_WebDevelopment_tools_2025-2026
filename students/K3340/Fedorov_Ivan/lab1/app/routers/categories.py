"""CRUD по категориям доходов/расходов."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.models import Category, CategoryKind, User
from app.schemas import (
    CategoryCreate,
    CategoryRead,
    CategoryReadWithTransactions,
    CategoryUpdate,
)
from db import get_session

router = APIRouter(prefix="/categories", tags=["Categories"])


def _get_own_category(
    category_id: int, session: Session, current_user: User
) -> Category:
    category = session.get(Category, category_id)
    if category is None or category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Категория не найдена"
        )
    return category


@router.get("/", response_model=List[CategoryRead])
def list_categories(
    kind: Optional[CategoryKind] = Query(default=None, description="Фильтр по типу"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Category]:
    query = select(Category).where(Category.user_id == current_user.id)
    if kind is not None:
        query = query.where(Category.kind == kind)
    return list(session.exec(query).all())


@router.get("/{category_id}", response_model=CategoryReadWithTransactions)
def get_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Category:
    """Категория с вложенными транзакциями и бюджетами (one-to-many)."""
    return _get_own_category(category_id, session, current_user)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = Category(**data.model_dump(), user_id=current_user.id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Category:
    category = _get_own_category(category_id, session, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    category = _get_own_category(category_id, session, current_user)
    session.delete(category)
    session.commit()
