"""Теги и управление связью many-to-many с транзакциями."""

from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.models import Tag, Transaction, TransactionTag, User
from app.schemas import (
    TagCreate,
    TagLinkInfo,
    TagRead,
    TagReadWithTransactions,
    TagUpdate,
)
from db import get_session

router = APIRouter(prefix="/tags", tags=["Tags"])


def _get_own_tag(tag_id: int, session: Session, current_user: User) -> Tag:
    tag = session.get(Tag, tag_id)
    if tag is None or tag.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Тег не найден")
    return tag


@router.get("/", response_model=List[TagRead])
def list_tags(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Tag]:
    return list(
        session.exec(select(Tag).where(Tag.user_id == current_user.id)).all()
    )


@router.get("/{tag_id}", response_model=TagReadWithTransactions)
def get_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    """Тег со списком транзакций (раскрытие many-to-many)."""
    return _get_own_tag(tag_id, session, current_user)


@router.post("/", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    data: TagCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    tag = Tag(name=data.name, user_id=current_user.id)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: int,
    data: TagUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Tag:
    tag = _get_own_tag(tag_id, session, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    tag = _get_own_tag(tag_id, session, current_user)
    # сначала чистим связи в ассоциативной таблице
    links = session.exec(
        select(TransactionTag).where(TransactionTag.tag_id == tag_id)
    ).all()
    for link in links:
        session.delete(link)
    session.delete(tag)
    session.commit()


@router.get(
    "/transaction/{transaction_id}/tags", response_model=List[TagLinkInfo]
)
def list_transaction_tags(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[TagLinkInfo]:
    """Теги транзакции вместе с доп. полями связи (note, added_at)."""
    tx = session.get(Transaction, transaction_id)
    if tx is None or tx.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    rows = session.exec(
        select(Tag, TransactionTag)
        .where(TransactionTag.transaction_id == transaction_id)
        .where(Tag.id == TransactionTag.tag_id)
    ).all()
    return [
        TagLinkInfo(id=tag.id, name=tag.name, note=link.note, added_at=link.added_at)
        for tag, link in rows
    ]


@router.post(
    "/transaction/{transaction_id}/tag/{tag_id}",
    response_model=TagLinkInfo,
    status_code=status.HTTP_201_CREATED,
)
def link_tag(
    transaction_id: int,
    tag_id: int,
    note: str = Body(default="", embed=True, description="Комментарий к связи"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TagLinkInfo:
    """Привязать тег к транзакции, заполнив поле связи note."""
    tx = session.get(Transaction, transaction_id)
    tag = _get_own_tag(tag_id, session, current_user)
    if tx is None or tx.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    if tag is None or tag.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Тег не найден")

    existing = session.get(TransactionTag, (transaction_id, tag_id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Тег уже привязан")

    link = TransactionTag(transaction_id=transaction_id, tag_id=tag_id, note=note)
    session.add(link)
    session.commit()
    session.refresh(link)
    return TagLinkInfo(
        id=tag.id, name=tag.name, note=link.note, added_at=link.added_at
    )


@router.patch(
    "/transaction/{transaction_id}/tag/{tag_id}", response_model=TagLinkInfo
)
def update_link_note(
    transaction_id: int,
    tag_id: int,
    note: str = Body(..., embed=True),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TagLinkInfo:
    """Обновить поле самой связи — то, чего нет у обычной m2m-таблицы."""
    tx = session.get(Transaction, transaction_id)
    if tx is None or tx.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    link = session.get(TransactionTag, (transaction_id, tag_id))
    if link is None:
        raise HTTPException(status_code=404, detail="Связь не найдена")

    link.note = note
    session.add(link)
    session.commit()
    session.refresh(link)
    tag = session.get(Tag, tag_id)
    return TagLinkInfo(
        id=tag.id, name=tag.name, note=link.note, added_at=link.added_at
    )


@router.delete(
    "/transaction/{transaction_id}/tag/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_tag(
    transaction_id: int,
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    tx = session.get(Transaction, transaction_id)
    if tx is None or tx.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    link = session.get(TransactionTag, (transaction_id, tag_id))
    if link is None:
        raise HTTPException(status_code=404, detail="Связь не найдена")
    session.delete(link)
    session.commit()
