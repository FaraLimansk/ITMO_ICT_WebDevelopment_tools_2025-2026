"""init: users, accounts, categories, transactions, budgets, goals, tags, transaction_tag

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-09-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("currency", sqlmodel.sql.sqltypes.AutoString(length=3), nullable=False),
        sa.Column("balance", sa.Float(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column(
            "kind",
            sa.Enum("income", "expense", name="categorykind"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_user_id", "categories", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("income", "expense", name="transactiontype"),
            nullable=False,
        ),
        sa.Column("comment", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("spent_at", sa.Date(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_spent_at", "transactions", ["spent_at"])
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("limit_amount", sa.Float(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_budgets_category_id", "budgets", ["category_id"])

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column("target_amount", sa.Float(), nullable=False),
        sa.Column("current_amount", sa.Float(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "reached", "cancelled", name="goalstatus"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tags_name", "tags", ["name"])
    op.create_index("ix_tags_user_id", "tags", ["user_id"])

    # ассоциативная сущность с доп. полями note и added_at
    op.create_table(
        "transaction_tag",
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("transaction_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("transaction_tag")
    op.drop_table("tags")
    op.drop_table("goals")
    op.drop_table("budgets")
    op.drop_table("transactions")
    op.drop_table("categories")
    op.drop_table("accounts")
    op.drop_table("users")
    sa.Enum(name="transactiontype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="categorykind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="goalstatus").drop(op.get_bind(), checkfirst=True)
