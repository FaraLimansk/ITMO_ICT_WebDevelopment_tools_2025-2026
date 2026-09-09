"""Pydantic/SQLModel-схемы для валидации входа и формирования ответов API.

Разделение на *Create / *Update / *Read нужно, чтобы клиент не мог передать
служебные поля (id, user_id, hashed_password) и чтобы в ответе не утекал хеш пароля.
Схемы *WithX — это GET-ответы с вложенными объектами (one-to-many и many-to-many).
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field as PydanticField, field_validator
from sqlmodel import SQLModel

from app.models import CategoryKind, GoalStatus, TransactionType


# ----------------------------- Auth / User --------------------------------
class UserCreate(SQLModel):
    username: str = PydanticField(min_length=3, max_length=64)
    email: EmailStr
    password: str = PydanticField(min_length=6, max_length=128)


class UserLogin(SQLModel):
    username: str
    password: str


class PasswordChange(SQLModel):
    old_password: str
    new_password: str = PydanticField(min_length=6, max_length=128)


class UserRead(SQLModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# ------------------------------- Account ----------------------------------
class AccountCreate(SQLModel):
    name: str = PydanticField(max_length=64)
    currency: str = "RUB"
    balance: float = 0.0

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3:
            raise ValueError("currency должен содержать 3 символа")
        return value


class AccountUpdate(SQLModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    balance: Optional[float] = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip().upper()
        if len(value) != 3:
            raise ValueError("currency должен содержать 3 символа")
        return value


class AccountRead(SQLModel):
    id: int
    name: str
    currency: str
    balance: float
    user_id: int


# ------------------------------ Category ----------------------------------
class CategoryCreate(SQLModel):
    name: str = PydanticField(max_length=64)
    kind: CategoryKind = CategoryKind.expense


class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    kind: Optional[CategoryKind] = None


class CategoryRead(SQLModel):
    id: int
    name: str
    kind: CategoryKind
    user_id: int


# -------------------------------- Tag -------------------------------------
class TagCreate(SQLModel):
    name: str = PydanticField(max_length=32)


class TagUpdate(SQLModel):
    name: Optional[str] = PydanticField(default=None, min_length=1, max_length=32)


class TagRead(SQLModel):
    id: int
    name: str
    user_id: int


class TagLinkInfo(SQLModel):
    """Тег вместе с данными самой связи (поля ассоциативной сущности)."""

    id: int
    name: str
    note: str
    added_at: datetime


# ----------------------------- Transaction --------------------------------
class TransactionCreate(SQLModel):
    amount: float = PydanticField(gt=0)
    type: TransactionType = TransactionType.expense
    comment: Optional[str] = None
    spent_at: Optional[date] = None
    account_id: int
    category_id: Optional[int] = None


class TransactionUpdate(SQLModel):
    amount: Optional[float] = PydanticField(default=None, gt=0)
    type: Optional[TransactionType] = None
    comment: Optional[str] = None
    spent_at: Optional[date] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None


class TransactionRead(SQLModel):
    id: int
    amount: float
    type: TransactionType
    comment: Optional[str]
    spent_at: date
    user_id: int
    account_id: int
    category_id: Optional[int]


class TransactionReadFull(TransactionRead):
    """Транзакция с вложенными объектами: счёт, категория и теги (m2m)."""

    account: Optional[AccountRead] = None
    category: Optional[CategoryRead] = None
    tags: List[TagRead] = PydanticField(default_factory=list)


class AccountReadWithTransactions(AccountRead):
    """Счёт со списком транзакций (one-to-many)."""

    transactions: List[TransactionRead] = PydanticField(default_factory=list)


class CategoryReadWithTransactions(CategoryRead):
    """Категория со списком транзакций и бюджетов (one-to-many)."""

    transactions: List[TransactionRead] = PydanticField(default_factory=list)
    budgets: List["BudgetRead"] = PydanticField(default_factory=list)


class TagReadWithTransactions(TagRead):
    """Тег со списком транзакций (many-to-many)."""

    transactions: List[TransactionRead] = PydanticField(default_factory=list)


# -------------------------------- Budget ----------------------------------
class BudgetCreate(SQLModel):
    limit_amount: float = PydanticField(gt=0)
    period_start: date
    period_end: date
    category_id: int


class BudgetUpdate(SQLModel):
    limit_amount: Optional[float] = PydanticField(default=None, gt=0)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    category_id: Optional[int] = None


class BudgetRead(SQLModel):
    id: int
    limit_amount: float
    period_start: date
    period_end: date
    user_id: int
    category_id: int


class BudgetReadWithCategory(BudgetRead):
    category: Optional[CategoryRead] = None


class BudgetStatus(SQLModel):
    """Состояние бюджета: сколько потрачено и есть ли превышение."""

    budget_id: int
    category_name: str
    limit_amount: float
    spent_amount: float
    remaining: float
    usage_percent: float
    is_exceeded: bool


# --------------------------------- Goal -----------------------------------
class GoalCreate(SQLModel):
    title: str = PydanticField(max_length=128)
    target_amount: float = PydanticField(gt=0)
    current_amount: float = 0.0
    deadline: Optional[date] = None


class GoalUpdate(SQLModel):
    title: Optional[str] = None
    target_amount: Optional[float] = PydanticField(default=None, gt=0)
    current_amount: Optional[float] = PydanticField(default=None, ge=0)
    deadline: Optional[date] = None
    status: Optional[GoalStatus] = None


class GoalRead(SQLModel):
    id: int
    title: str
    target_amount: float
    current_amount: float
    deadline: Optional[date]
    status: GoalStatus
    user_id: int


class UserReadFull(UserRead):
    """Профиль со всеми вложенными коллекциями (one-to-many)."""

    accounts: List[AccountRead] = PydanticField(default_factory=list)
    categories: List[CategoryRead] = PydanticField(default_factory=list)
    transactions: List[TransactionRead] = PydanticField(default_factory=list)
    budgets: List[BudgetRead] = PydanticField(default_factory=list)
    goals: List[GoalRead] = PydanticField(default_factory=list)
    tags: List[TagRead] = PydanticField(default_factory=list)


# ------------------------------- Отчёты ------------------------------------
class CategorySummary(BaseModel):
    category_id: Optional[int]
    category_name: str
    total: float
    share_percent: float


class PeriodReport(BaseModel):
    period_start: date
    period_end: date
    total_income: float
    total_expense: float
    balance: float
    by_category: List[CategorySummary]


# Обновляем forward-ref в CategoryReadWithTransactions
CategoryReadWithTransactions.model_rebuild()
