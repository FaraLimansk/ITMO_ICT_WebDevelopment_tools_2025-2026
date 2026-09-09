"""CRUD по транзакциям + автоматический пересчёт баланса счёта."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.models import Account, Category, Transaction, TransactionType, User
from app.schemas import (
    TransactionCreate,
    TransactionRead,
    TransactionReadFull,
    TransactionUpdate,
)
from db import get_session

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _signed(amount: float, tx_type: TransactionType) -> float:
    """Знак влияния операции на баланс: доход — плюс, расход — минус."""
    return amount if tx_type == TransactionType.income else -amount


def _get_own_transaction(
    transaction_id: int, session: Session, current_user: User
) -> Transaction:
    tx = session.get(Transaction, transaction_id)
    if tx is None or tx.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Транзакция не найдена"
        )
    return tx


def _check_refs(
    session: Session,
    current_user: User,
    account_id: Optional[int],
    category_id: Optional[int],
    tx_type: Optional[TransactionType] = None,
) -> None:
    """Проверяет, что счёт и категория существуют и принадлежат пользователю."""
    if account_id is not None:
        account = session.get(Account, account_id)
        if account is None or account.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Некорректный account_id")
    if category_id is not None:
        category = session.get(Category, category_id)
        if category is None or category.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Некорректный category_id")
        if tx_type is not None and category.kind.value != tx_type.value:
            raise HTTPException(
                status_code=400,
                detail="Тип транзакции должен совпадать с типом категории",
            )


@router.get("/", response_model=List[TransactionReadFull])
def list_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Transaction]:
    """Список операций с фильтрами; в ответе вложены счёт, категория и теги."""
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)
    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)
    if date_from is not None:
        query = query.where(Transaction.spent_at >= date_from)
    if date_to is not None:
        query = query.where(Transaction.spent_at <= date_to)
    query = query.order_by(Transaction.spent_at.desc()).offset(skip).limit(limit)
    return list(session.exec(query).all())


@router.get("/{transaction_id}", response_model=TransactionReadFull)
def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    """Одна операция со связанными объектами (one-to-many и many-to-many)."""
    return _get_own_transaction(transaction_id, session, current_user)


@router.post(
    "/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED
)
def create_transaction(
    data: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    _check_refs(session, current_user, data.account_id, data.category_id, data.type)

    payload = data.model_dump()
    if payload.get("spent_at") is None:
        payload["spent_at"] = date.today()

    tx = Transaction(**payload, user_id=current_user.id)
    session.add(tx)

    # баланс счёта держим согласованным с операциями
    account = session.get(Account, tx.account_id)
    account.balance += _signed(tx.amount, tx.type)
    session.add(account)

    session.commit()
    session.refresh(tx)
    return tx


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    data: TransactionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Transaction:
    tx = _get_own_transaction(transaction_id, session, current_user)
    updates = data.model_dump(exclude_unset=True)
    resulting_category_id = updates.get("category_id", tx.category_id)
    resulting_type = updates.get("type", tx.type)
    _check_refs(
        session,
        current_user,
        updates.get("account_id"),
        resulting_category_id,
        resulting_type,
    )

    # сначала отменяем старое влияние на баланс
    old_account = session.get(Account, tx.account_id)
    old_account.balance -= _signed(tx.amount, tx.type)
    session.add(old_account)

    for field, value in updates.items():
        setattr(tx, field, value)

    # затем применяем новое (счёт мог поменяться)
    new_account = session.get(Account, tx.account_id)
    new_account.balance += _signed(tx.amount, tx.type)
    session.add(new_account)

    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    tx = _get_own_transaction(transaction_id, session, current_user)
    account = session.get(Account, tx.account_id)
    account.balance -= _signed(tx.amount, tx.type)
    session.add(account)
    session.delete(tx)
    session.commit()
