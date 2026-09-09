"""ORM-модели (SQLModel) сервиса управления личными финансами.

Таблицы (8 шт.):
    users, accounts, categories, transactions, budgets, goals, tags,
    transaction_tag (ассоциативная сущность с доп. полями).

Связи:
    one-to-many:  User -> Account / Transaction / Budget / Goal,
                  Account -> Transaction, Category -> Transaction / Budget
    many-to-many: Transaction <-> Tag через transaction_tag
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class TransactionType(str, Enum):
    """Тип денежной операции."""

    income = "income"    # доход
    expense = "expense"  # расход


class CategoryKind(str, Enum):
    """Направление категории."""

    income = "income"
    expense = "expense"


class GoalStatus(str, Enum):
    """Статус финансовой цели."""

    active = "active"
    reached = "reached"
    cancelled = "cancelled"


# --------------------------------------------------------------------------
# Ассоциативная сущность many-to-many с собственными полями
# --------------------------------------------------------------------------
class TransactionTag(SQLModel, table=True):
    """Связь «транзакция — тег».

    Помимо двух внешних ключей содержит поля, характеризующие саму связь:
    ``note`` (комментарий, зачем повешен тег) и ``added_at`` (когда повешен).
    """

    __tablename__ = "transaction_tag"

    transaction_id: Optional[int] = Field(
        default=None, foreign_key="transactions.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="tags.id", primary_key=True
    )
    note: str = Field(default="", max_length=255)
    added_at: datetime = Field(default_factory=datetime.utcnow)


# --------------------------------------------------------------------------
# Основные таблицы
# --------------------------------------------------------------------------
class User(SQLModel, table=True):
    """Пользователь сервиса."""

    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=64)
    email: str = Field(index=True, unique=True, max_length=128)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    accounts: List["Account"] = Relationship(back_populates="user")
    categories: List["Category"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    budgets: List["Budget"] = Relationship(back_populates="user")
    goals: List["Goal"] = Relationship(back_populates="user")
    tags: List["Tag"] = Relationship(back_populates="user")


class Account(SQLModel, table=True):
    """Счёт/кошелёк пользователя (наличные, карта, вклад...)."""

    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=64)
    currency: str = Field(default="RUB", max_length=3)
    balance: float = Field(default=0.0)
    user_id: int = Field(foreign_key="users.id", index=True)

    user: Optional[User] = Relationship(back_populates="accounts")
    transactions: List["Transaction"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Category(SQLModel, table=True):
    """Категория доходов или расходов."""

    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=64, index=True)
    kind: CategoryKind = Field(default=CategoryKind.expense)
    user_id: int = Field(foreign_key="users.id", index=True)

    user: Optional[User] = Relationship(back_populates="categories")
    transactions: List["Transaction"] = Relationship(back_populates="category")
    budgets: List["Budget"] = Relationship(
        back_populates="category",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Transaction(SQLModel, table=True):
    """Денежная операция: доход или расход по конкретному счёту."""

    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    type: TransactionType = Field(default=TransactionType.expense)
    comment: Optional[str] = Field(default=None, max_length=255)
    spent_at: date = Field(default_factory=date.today, index=True)

    user_id: int = Field(foreign_key="users.id", index=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    category_id: Optional[int] = Field(
        default=None, foreign_key="categories.id", index=True
    )

    user: Optional[User] = Relationship(back_populates="transactions")
    account: Optional[Account] = Relationship(back_populates="transactions")
    category: Optional[Category] = Relationship(back_populates="transactions")
    tags: List["Tag"] = Relationship(
        back_populates="transactions", link_model=TransactionTag
    )


class Budget(SQLModel, table=True):
    """Лимит трат по категории на период."""

    __tablename__ = "budgets"

    id: Optional[int] = Field(default=None, primary_key=True)
    limit_amount: float
    period_start: date
    period_end: date
    user_id: int = Field(foreign_key="users.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)

    user: Optional[User] = Relationship(back_populates="budgets")
    category: Optional[Category] = Relationship(back_populates="budgets")


class Goal(SQLModel, table=True):
    """Финансовая цель (накопить N рублей к дате)."""

    __tablename__ = "goals"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=128)
    target_amount: float
    current_amount: float = Field(default=0.0)
    deadline: Optional[date] = Field(default=None, index=True)
    status: GoalStatus = Field(default=GoalStatus.active)
    user_id: int = Field(foreign_key="users.id", index=True)

    user: Optional[User] = Relationship(back_populates="goals")


class Tag(SQLModel, table=True):
    """Метка, которую можно навесить на несколько транзакций."""

    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=32, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    user: Optional[User] = Relationship(back_populates="tags")
    transactions: List[Transaction] = Relationship(
        back_populates="tags", link_model=TransactionTag
    )
