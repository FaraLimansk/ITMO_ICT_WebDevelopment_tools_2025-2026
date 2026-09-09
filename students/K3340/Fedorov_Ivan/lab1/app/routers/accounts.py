"""CRUD по счетам пользователя."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.models import Account, User
from app.schemas import (
    AccountCreate,
    AccountRead,
    AccountReadWithTransactions,
    AccountUpdate,
)
from db import get_session

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def _get_own_account(
    account_id: int, session: Session, current_user: User
) -> Account:
    """Вспомогательная функция: счёт есть и он принадлежит текущему пользователю."""
    account = session.get(Account, account_id)
    if account is None or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Счёт не найден"
        )
    return account


@router.get("/", response_model=List[AccountRead])
def list_accounts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Account]:
    return list(
        session.exec(
            select(Account).where(Account.user_id == current_user.id)
        ).all()
    )


@router.get("/{account_id}", response_model=AccountReadWithTransactions)
def get_account(
    account_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    """Счёт с вложенным списком транзакций (one-to-many)."""
    return _get_own_account(account_id, session, current_user)


@router.post("/", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    account = Account(**data.model_dump(), user_id=current_user.id)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: int,
    data: AccountUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Account:
    account = _get_own_account(account_id, session, current_user)
    # exclude_unset — патчим только те поля, которые пришли в теле запроса
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    account = _get_own_account(account_id, session, current_user)
    session.delete(account)
    session.commit()
